import os
import json
import boto3
import pika
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image
import cv2
import io
import requests
import argparse
import base64
import urllib.request
import tempfile
from dotenv import load_dotenv
from utils.utils import *
load_dotenv()
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-2")

s3 = boto3.client("s3", region_name=AWS_REGION)

class DOLPHINClient:
    def __init__(self, endpoint_name="dolphin-endpoint", region_name="us-east-1"):
        self.endpoint = endpoint_name
        self.client = boto3.client('sagemaker-runtime', region_name=region_name)

    def chat(self, prompt, image):
        """Invoke the SageMaker endpoint with prompt and image (single or batch)."""

        # Normalize batch
        is_batch = isinstance(image, list)
        images = image if is_batch else [image]
        prompts = prompt if isinstance(prompt, list) else [prompt] * len(images)

        encoded_images = []
        for img in images:
            # Convert PIL image to base64
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG")
            img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            encoded_images.append(img_b64)

        # For batch, bundle into list
        body = json.dumps({
            "image": encoded_images,
            "prompt": prompts
        })

        response = self.client.invoke_endpoint(
            EndpointName=self.endpoint,
            ContentType="application/json",
            Body=body
        )

        result_str = response['Body'].read().decode('utf-8')
        data = json.loads(result_str)
        outputs = data.get("output", [])
        if not is_batch and isinstance(outputs, list) and len(outputs) == 1:
            return outputs[0]
        elif is_batch and not isinstance(outputs, list):
            return [outputs]
        return outputs


def download_file_from_url(url: str) -> str:
    """
    Download a file from a URL to a temporary location.
    
    Args:
        url: The URL of the file to download
        
    Returns:
        str: Path to the downloaded temporary file
    """
    temp_fd, temp_path = tempfile.mkstemp(suffix=os.path.splitext(url)[1])
    os.close(temp_fd)  # Close the file descriptor
    logger.info(f"Downloading file from URL: {url}")
    try:
        urllib.request.urlretrieve(url, temp_path)
        logger.info(f"Successfully downloaded file to temporary location: {temp_path}")
        return temp_path
    except Exception as e:
        logger.error(f"Failed to download file from {url}: {e}")
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def process_document(document_path, model, save_dir, max_batch_size=None):
    """Parse documents with two stages - Handles both images and PDFs"""
    file_ext = os.path.splitext(document_path)[1].lower()
    
    if file_ext == '.pdf':
        # Process PDF file
        # Convert PDF to images
        images = convert_pdf_to_images(document_path)
        if not images:
            raise Exception(f"Failed to convert PDF {document_path} to images")
        
        all_results = []
        
        # Process each page
        for page_idx, pil_image in enumerate(images):
            print(f"Processing page {page_idx + 1}/{len(images)}")
            
            # Generate output name for this page
            base_name = os.path.splitext(os.path.basename(document_path))[0]
            page_name = f"{base_name}_page_{page_idx + 1:03d}"
            
            # Process this page (don't save individual page results)
            json_path, recognition_results = process_single_image(
                pil_image, model, save_dir, page_name, max_batch_size, save_individual=False
            )
            
            # Add page information to results
            page_results = {
                "page_number": page_idx + 1,
                "elements": recognition_results
            }
            all_results.append(page_results)
        
        # Save combined results for multi-page PDF
        combined_json_path = save_combined_pdf_results(all_results, document_path, save_dir)
        
        return combined_json_path, all_results
    
    else:
        # Process regular image file
        pil_image = Image.open(document_path).convert("RGB")
        base_name = os.path.splitext(os.path.basename(document_path))[0]
        return process_single_image(pil_image, model, save_dir, base_name, max_batch_size)


def process_single_image(image, model, save_dir, image_name, max_batch_size=None, save_individual=True):
    """Process a single image (either from file or converted from PDF page)
    
    Args:
        image: PIL Image object
        model: DOLPHIN model instance
        save_dir: Directory to save results
        image_name: Name for the output file
        max_batch_size: Maximum batch size for processing
        save_individual: Whether to save individual results (False for PDF pages)
        
    Returns:
        Tuple of (json_path, recognition_results)
    """
    # Stage 1: Page-level layout and reading order parsing
    layout_output = model.chat("Parse the reading order of this document.", image)

    # Stage 2: Element-level content parsing
    padded_image, dims = prepare_image(image)
    recognition_results = process_elements(layout_output, padded_image, dims, model, max_batch_size, save_dir, image_name)

    # Save outputs only if requested (skip for PDF pages)
    json_path = None
    if save_individual:
        # Ensure output directories exist
        setup_output_dirs(save_dir)
        # Create a dummy image path for save_outputs function
        dummy_image_path = f"{image_name}.jpg"  # Extension doesn't matter, only basename is used
        json_path = save_outputs(recognition_results, dummy_image_path, save_dir)

    return json_path, recognition_results


def process_elements(layout_results, padded_image, dims, model, max_batch_size, save_dir=None, image_name=None):
    """Parse all document elements with parallel decoding"""
    layout_results = parse_layout_string(layout_results)

    # Store text and table elements separately
    text_elements = []  # Text elements
    table_elements = []  # Table elements
    figure_results = []  # Image elements (no processing needed)
    previous_box = None
    reading_order = 0

    # Collect elements to process and group by type
    for bbox, label in layout_results:
        try:
            # Adjust coordinates
            x1, y1, x2, y2, orig_x1, orig_y1, orig_x2, orig_y2, previous_box = process_coordinates(
                bbox, padded_image, dims, previous_box
            )

            # Crop and parse element
            cropped = padded_image[y1:y2, x1:x2]
            if cropped.size > 0 and cropped.shape[0] > 3 and cropped.shape[1] > 3:
                if label == "fig":
                    pil_crop = Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
                    
                    figure_filename = save_figure_to_local(pil_crop, save_dir, image_name, reading_order)
                    
                    # For figure regions, store relative path instead of base64
                    figure_results.append(
                        {
                            "label": label,
                            "text": f"![Figure]({figure_filename})",
                            "figure_path": f"figures/{figure_filename}",
                            "bbox": [orig_x1, orig_y1, orig_x2, orig_y2],
                            "reading_order": reading_order,
                        }
                    )
                else:
                    # Prepare element for parsing
                    pil_crop = Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
                    element_info = {
                        "crop": pil_crop,
                        "label": label,
                        "bbox": [orig_x1, orig_y1, orig_x2, orig_y2],
                        "reading_order": reading_order,
                    }
                    
                    # Group by type
                    if label == "tab":
                        table_elements.append(element_info)
                    else:  # Text elements
                        text_elements.append(element_info)

            reading_order += 1

        except Exception as e:
            print(f"Error processing bbox with label {label}: {str(e)}")
            continue

    # Initialize results list
    recognition_results = figure_results.copy()
    
    # Process text elements (in batches)
    if text_elements:
        text_results = process_element_batch(text_elements, model, "Read text in the image.", max_batch_size)
        recognition_results.extend(text_results)
    
    # Process table elements (in batches)
    if table_elements:
        table_results = process_element_batch(table_elements, model, "Parse the table in the image.", max_batch_size)
        recognition_results.extend(table_results)

    # Sort elements by reading order
    recognition_results.sort(key=lambda x: x.get("reading_order", 0))

    return recognition_results


def process_element_batch(elements, model, prompt, max_batch_size=None):
    """Process elements of the same type in batches"""
    results = []
    
    # Determine batch size
    batch_size = len(elements)
    if max_batch_size is not None and max_batch_size > 0:
        batch_size = min(batch_size, max_batch_size)
    
    # Process in batches
    for i in range(0, len(elements), batch_size):
        batch_elements = elements[i:i+batch_size]
        crops_list = [elem["crop"] for elem in batch_elements]
        
        # Use the same prompt for all elements in the batch
        prompts_list = [prompt] * len(crops_list)
        
        # Batch inference
        batch_results = model.chat(prompts_list, crops_list)
        # Add results
        for j, result in enumerate(batch_results):
            elem = batch_elements[j]
            results.append({
                "label": elem["label"],
                "bbox": elem["bbox"],
                "text": result.strip(),
                "reading_order": elem["reading_order"],
            })
    
    return results

class OCRParserService:
    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None
        self.s3_client = boto3.client('s3')
        
        # Initialize DOLPHIN client
        self.model = DOLPHINClient(
            endpoint_name=os.getenv('DOLPHIN_ENDPOINT', 'dolphin-endpoint'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )

    def connect(self):
        """Establish connection to RabbitMQ."""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            params = pika.URLParameters(self.rabbitmq_url)
            params.heartbeat = 200  # Keep alive every 30s
            params.frame_max = 131072
            params.blocked_connection_timeout = 300
            params.connection_attempts = 5
            params.retry_delay = 2.0
            self.connection = pika.BlockingConnection(params)
            
            self.channel = self.connection.channel()
            
            # Declare queues
            self.channel.queue_declare(queue='pdf-parser-queue', durable=True)
            self.channel.queue_declare(queue='chunking-queue', durable=True)
            
            logger.info("✅ Connected to RabbitMQ and listening on pdf-parser-queue")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def download_file_from_url(self, url: str) -> Optional[str]:
        """Download a file from URL to a temporary location."""
        try:
            logger.info(f"Downloading from URL: {url}")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            with open(temp_file.name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded to: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            return None

    def upload_to_s3(self, local_path: str, bucket: str, s3_key: str) -> None:
        """Upload a file to S3."""
        try:
            self.s3_client.upload_file(str(local_path), bucket, s3_key)
            logger.info(f"Uploaded {local_path} to s3://{bucket}/{s3_key}")
        except Exception as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise
    def _ensure_connection(self):
        if self.connection is None or self.connection.is_closed:
            self.connect()
        if self.channel is None or self.channel.is_closed:
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue_name, durable=True)
    def process_message(self, ch, method, properties, body):
        """Process incoming message from the queue."""
        try:
            message = json.loads(body)
            logger.info(f"📩 Received message: {message}")
            
            # Extract necessary information from payload
            s3_key = message.get('s3Key') or message.get('file_url')
            filename = message.get('filename', os.path.basename(s3_key) if s3_key else 'unknown')
            document_id = message.get('documentId', "")
            s3_bucket = message.get('s3Bucket') or os.getenv('S3_BUCKET_NAME')
            
            if not s3_key or not s3_bucket:
                raise ValueError("Missing required parameters (s3Key/file_url and s3Bucket)")
            
            # Use same S3 path structure as DOCX parser: parsed/{document_id}/
            base_filename = os.path.splitext(filename)[0]
            markdown_s3_key = f"parsed/{document_id}/{base_filename}.md"
            
            logger.info(f"🚀 Processing PDF file: {filename}")
            logger.info(f"📝 Will generate markdown at: {markdown_s3_key}")
            file_type = message.get('fileType', 'pdf')
    
            # Determine file extension
            if file_type == 'image':
                # For images, detect extension from s3_key or use generic
                if '.' in s3_key:
                    ext = '.' + s3_key.split('.')[-1]
                else:
                    ext = '.jpg'  # default
            else:
                ext = '.pdf'
            # Download the file if it's a URL
            if s3_key.startswith(('http://', 'https://')):
                temp_file = self.download_file_from_url(s3_key)
                if not temp_file:
                    raise Exception("Failed to download file from URL")
                file_path = temp_file
            else:
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_file:
                    print(f"[DEBUG] Downloading {s3_key} from S3 to {tmp_file.name}")
                    s3.download_fileobj(s3_bucket, s3_key, tmp_file)
                    tmp_file_path = tmp_file.name
                file_path = tmp_file_path
            # Process the document
            result = self.process_document_with_ocr(    
                file_url=file_path,
                s3_bucket=s3_bucket,
                s3_key=markdown_s3_key,
                document_id=document_id
            )
            print(result['s3_keys'])
            # Verify that we have a valid markdown key
            if 'markdown' not in result['s3_keys']:
                raise ValueError("No markdown file was generated during processing")
                
            # Prepare result for chunking queue
            chunking_payload = {
                's3Bucket': s3_bucket,
                's3Key': markdown_s3_key,
                'documentId': document_id,
                'fileType': 'pdf'
            }
            
            logger.info(f"Sending to chunking queue: {chunking_payload}")
            # Send to chunking queue
            self.channel.basic_publish(
                exchange='',
                routing_key='chunking-queue',
                body=json.dumps(chunking_payload),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                )
            )
            
            logger.info(f"✅ Successfully processed {filename}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except (pika.exceptions.StreamLostError, pika.exceptions.ConnectionClosed) as e:
            logger.warning("🔁 RabbitMQ connection lost. Attempting to reconnect...")
            self.connect()
            self.channel.basic_publish(
                exchange='',
                routing_key='chunking-queue',
                body=json.dumps(chunking_payload),
                properties=pika.BasicProperties(delivery_mode=2),
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}", exc_info=True)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def process_document_with_ocr(self, file_url: str, s3_bucket: str, s3_key: str, document_id: str) -> Dict[str, Any]:
        """Process a document with the DOLPHIN OCR model and upload results to S3."""
        temp_file = None
        
        try:
            

            # Create a temporary directory for output
            with tempfile.TemporaryDirectory() as temp_dir:
                # Process the document using DOLPHIN OCR
                json_path, recognition_results = process_document(
                    document_path=file_url,
                    model=self.model,
                    save_dir=temp_dir,
                    max_batch_size=int(os.getenv('MAX_BATCH_SIZE', '8'))
                )
                
                if not json_path or not os.path.exists(json_path):
                    raise Exception("Failed to process document - no output generated")
                
                # Upload results to S3
                s3_keys = {}
                
                # Upload markdown file directly to the specified S3 key
                md_path = json_path.replace('.json', '.md').replace('recognition_json', 'markdown')
                if not os.path.exists(md_path):
                    logger.error(f"Markdown file not found at expected path: {md_path}")
                    # Try to find the markdown file in the temp directory
                    md_dir = os.path.dirname(md_path)
                    for file in os.listdir(md_dir):
                        if file.endswith('.md'):
                            md_path = os.path.join(md_dir, file)
                            logger.info(f"Found markdown file at alternative path: {md_path}")
                            break
                
                if os.path.exists(md_path):
                    logger.info(f"Uploading markdown to s3://{s3_bucket}/{s3_key}")
                    self.upload_to_s3(md_path, s3_bucket, s3_key)
                    s3_keys['markdown'] = f"s3://{s3_bucket}/{s3_key}"
                else:
                    logger.error(f"Could not find markdown file after processing. Checked: {md_path}")
                    # Create a minimal markdown file with error message
                    md_content = "# Error\n\nFailed to generate markdown content during processing."
                    with open(md_path, 'w') as f:
                        f.write(md_content)
                    logger.info(f"Uploading error markdown to s3://{s3_bucket}/{s3_key}")
                    self.upload_to_s3(md_path, s3_bucket, s3_key)
                    s3_keys['markdown'] = f"s3://{s3_bucket}/{s3_key}"
                
                # Upload any generated figures
                figures_dir = os.path.join(temp_dir, 'markdown', 'figures')
                if os.path.exists(figures_dir):
                    s3_keys['figures'] = []
                    # Use same structure as DOCX: parsed/{document_id}/figures/
                    for fig_file in os.listdir(figures_dir):
                        fig_path = os.path.join(figures_dir, fig_file)
                        fig_key = f"parsed/{document_id}/figures/{fig_file}"
                        self.upload_to_s3(fig_path, s3_bucket, fig_key)
                        s3_keys['figures'].append(f"s3://{s3_bucket}/{fig_key}")
                
                return {
                    'status': 'success',
                    's3_keys': s3_keys,
                    'document_id': os.path.splitext(os.path.basename(file_url))[0]
                }
                
        except Exception as e:
            logger.error(f"Error processing document: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'document_id': os.path.splitext(os.path.basename(file_url))[0] if 'file_url' in locals() else 'unknown'
            }
            
        finally:
            # Clean up temporary file if it was created
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_file}: {e}")


def main():
    parser = argparse.ArgumentParser(description='Run DOLPHIN OCR worker')
    parser.add_argument('--rabbitmq', type=str, 
                       default=os.getenv('RABBITMQ_URL', 'amqp://admin:admin@52.65.216.159:5672'),
                       help='RabbitMQ connection URL')
    
    args = parser.parse_args()
    
    # Initialize and start the service
    service = OCRParserService(rabbitmq_url=args.rabbitmq)
    service.connect()
    
    # Declare queues
    service.channel.queue_declare(queue='pdf-parser-queue', durable=True)
    service.channel.queue_declare(queue='chunking-queue', durable=True)
    
    # Set up consumer
    service.channel.basic_qos(prefetch_count=1)
    service.channel.basic_consume(
        queue='pdf-parser-queue',
        on_message_callback=service.process_message,
        auto_ack=False
    )
    
    try:
        logger.info("🚀 Starting DOLPHIN OCR worker...")
        logger.info("🔄 Waiting for messages in pdf-parser-queue...")
        service.channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down worker...")
        service.channel.stop_consuming()
    except Exception as e:
        logger.error(f"❌ Error in consumer: {e}")
    finally:
        if service.connection and service.connection.is_open:
            service.connection.close()

if __name__ == "__main__":
    main()