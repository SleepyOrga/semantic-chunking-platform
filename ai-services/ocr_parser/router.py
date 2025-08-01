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
import fitz  # PyMuPDF
from langdetect import detect
import sys

def extract_text_from_pdf(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def detect_language_from_pdf(pdf_path: str):
    try:
        text = extract_text_from_pdf(pdf_path)
        if not text.strip():
            return "Empty or unreadable content"
        lang = detect(text)
        return lang
    except Exception as e:
        return f"Error: {str(e)}"

s3 = boto3.client("s3", region_name=AWS_REGION)
bedrock_client = boto3.client('bedrock-runtime', region_name=AWS_REGION)


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


class OCRParserService:
    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None
        self.s3_client = boto3.client('s3')

    def connect(self):
        """Establish connection to RabbitMQ."""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            params = pika.URLParameters(self.rabbitmq_url)
            params.heartbeat = 300  # Keep alive every 30s
            params.frame_max = 131072
            params.blocked_connection_timeout = 300
            params.connection_attempts = 5
            params.retry_delay = 2.0
            self.connection = pika.BlockingConnection(params)
            
            self.channel = self.connection.channel()
            
            # Declare queues
            self.channel.queue_declare(queue='pdf-parser-queue', durable=True)
            self.channel.queue_declare(queue='pdf-english-parser-queue', durable=True)
            self.channel.queue_declare(queue='pdf-other-parser-queue', durable=True)
            
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
            
            if ext == '.pdf':
                language = detect_language_from_pdf(file_path)
                if language == "en":
                    queue_name = 'pdf-english-parser-queue'
                else:
                    queue_name = 'pdf-other-parser-queue'
            else:
                queue_name = 'pdf-english-parser-queue'
            
            # Send to chunking queue
            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=body,
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
                print("ok 2")
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