import os
import tempfile
import argparse
import boto3
import json
import pika
from pathlib import Path
from typing import Dict, Any, Optional
from huggingface_hub import snapshot_download
from docling_core.types.doc import ImageRefMode, TableItem, PictureItem
import requests
import logging

from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
from docling.datamodel.settings import settings
from docling.document_converter import DocumentConverter, PdfFormatOption

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OcrParserService:
    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None
        self.s3_client = boto3.client('s3')
        self.IMAGE_RESOLUTION_SCALE = 2.0
        
        # Initialize document converter
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=PdfPipelineOptions(
                        rapid_ocr_options=RapidOcrOptions(
                            use_gpu=False,
                            image_resolution_scale=self.IMAGE_RESOLUTION_SCALE,
                        ),
                        accelerator_options=AcceleratorOptions(
                            device=AcceleratorDevice.CPU,
                            device_ids=None,
                        ),
                        table_detection_enabled=True,
                        image_ref_mode=ImageRefMode.EMBEDDED,
                    ),
                ),
            },
        )

    def connect(self):
        """Establish connection to RabbitMQ."""
        try:
            self.connection = pika.BlockingConnection(
                pika.URLParameters(self.rabbitmq_url)
            )
            self.channel = self.connection.channel()
            
            # Declare queues
            self.channel.queue_declare(queue='pdf-other-parser-queue', durable=True)
            self.channel.queue_declare(queue='chunking-queue', durable=True)
            
            logger.info("✅ Connected to RabbitMQ and listening on pdf-other-parser-queue")
            
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

    def process_document(self, input_file: str, output_dir: str, s3_bucket: str = None, s3_prefix: str = None) -> str:
        """Process a single document and return the S3 key or local path of the result."""
        temp_file = None
        try:
            # If input_file is a URL, download it first
            if input_file.startswith(("http://", "https://")):
                temp_file = self.download_file_from_url(input_file)
                if not temp_file:
                    raise Exception("Failed to download file from URL")
                input_file = temp_file

            input_path = Path(input_file)
            if not input_path.exists():
                raise FileNotFoundError(f"Input file not found: {input_path}")

            # Create output directory
            output_dir_path = Path(output_dir)
            output_dir_path.mkdir(parents=True, exist_ok=True)
            
            # Process the document
            logger.info(f"Processing document: {input_path}")
            output_path = output_dir_path / f"{input_path.stem}.md"
            
            # Convert the document
            result = self.converter.convert(input_path)
            
            # Save markdown
            markdown_content = result.document.export_to_markdown()
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            logger.info(f"✅ Saved markdown: {output_path}")
            
            # Save full-page images, tables, and figures
            doc_filename = result.input.file.stem
            
            # Save full-page images
            for page_no, page in result.document.pages.items():
                image_path = output_dir_path / f"{doc_filename}-{page_no}.png"
                with open(image_path, 'wb') as f:
                    page.image.pil_image.save(f, format="PNG")
                
                # Upload to S3 if configured
                if s3_bucket and s3_prefix:
                    img_key = f"{s3_prefix}images/{image_path.name}"
                    self.upload_to_s3(image_path, s3_bucket, img_key)
            
            # Save tables and figures
            table_counter = 0
            picture_counter = 0
            
            for element, _ in result.document.iterate_items():
                if isinstance(element, TableItem):
                    table_counter += 1
                    image_path = output_dir_path / f"{doc_filename}-table-{table_counter}.png"
                    with open(image_path, 'wb') as f:
                        element.get_image(result.document).save(f, "PNG")
                    
                    # Upload to S3 if configured
                    if s3_bucket and s3_prefix:
                        img_key = f"{s3_prefix}tables/{image_path.name}"
                        self.upload_to_s3(image_path, s3_bucket, img_key)
                
                elif isinstance(element, PictureItem):
                    picture_counter += 1
                    image_path = output_dir_path / f"{doc_filename}-picture-{picture_counter}.png"
                    with open(image_path, 'wb') as f:
                        element.get_image(result.document).save(f, "PNG")
                    
                    # Upload to S3 if configured
                    if s3_bucket and s3_prefix:
                        img_key = f"{s3_prefix}pictures/{image_path.name}"
                        self.upload_to_s3(image_path, s3_bucket, img_key)
            
            # Upload markdown to S3 if configured
            s3_key = None
            if s3_bucket and s3_prefix:
                s3_key = f"{s3_prefix}{output_path.name}"
                self.upload_to_s3(output_path, s3_bucket, s3_key)
            
            return s3_key or str(output_path)
            
        except Exception as e:
            logger.error(f"Error processing document: {e}", exc_info=True)
            raise
            
        finally:
            # Clean up temporary file if it was created
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_file}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Run OCR PDF parser worker')
    parser.add_argument('--rabbitmq', type=str, 
                       default='amqp://admin:admin@52.65.216.159:5672',
                       help='RabbitMQ connection URL')
    
    args = parser.parse_args()
    
    # Create and start worker
    worker = OcrParserService(args.rabbitmq)
    worker.connect()
    worker.start_consuming()

if __name__ == "__main__":
    main()
