import os
import tempfile
import argparse
import boto3
from pathlib import Path
import requests
import logging
import json
import pika
from typing import Dict, Any, Optional

# Import required docling modules
from docling.document_converter import DocumentConverter, ExcelFormatOption
from docling.datamodel.base_models import InputFormat
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.backend.msexcel_backend import MsExcelDocumentBackend

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class XlsxParserService:
    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None
        self.s3_client = boto3.client('s3')

    def connect(self):
        """Establish connection to RabbitMQ."""
        try:
            self.connection = pika.BlockingConnection(
                pika.URLParameters(self.rabbitmq_url)
            )
            self.channel = self.connection.channel()
            
            # Declare queues
            self.channel.queue_declare(queue='xlsx-parser-queue', durable=True)
            self.channel.queue_declare(queue='chunking-queue', durable=True)
            
            logger.info("✅ Connected to RabbitMQ and listening on xlsx-parser-queue")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

def download_file_from_url(url):
    try:
        logging.info(f"Downloading from URL: {url}")
        response = requests.get(url)
        response.raise_for_status()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        with open(temp_file.name, 'wb') as f:
            f.write(response.content)
        logging.info(f"Downloaded to: {temp_file.name}")
        return temp_file.name
    except Exception as e:
        logging.info(f"Failed to download file: {e}")
        return None

def upload_to_s3(local_path, bucket, s3_key):
    s3 = boto3.client('s3')
    s3.upload_file(str(local_path), bucket, s3_key)
    logging.info(f"Uploaded {local_path} to s3://{bucket}/{s3_key}")

def extract_xlsx_to_markdown(input_path, output_dir, s3_bucket=None, s3_prefix=None):
    try:
        os.makedirs(output_dir, exist_ok=True)
        images_dir = os.path.join(output_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        
        # Initialize the document converter
        converter = DocumentConverter(
            format_options={
                InputFormat.XLSX: ExcelFormatOption(
                    pipeline_cls=SimplePipeline,
                    backend=MsExcelDocumentBackend
                )
            }
        )
        
        # Handle input path (could be a file path or URL)
        local_path = input_path
        if isinstance(input_path, str) and (input_path.startswith("http://") or input_path.startswith("https://")):
            local_path = download_file_from_url(input_path)
            if not local_path:
                raise Exception("Failed to download file from URL")
        
        input_path = Path(local_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
            
        # Process the file
        logging.info(f"Processing {input_path.name}")
        result = converter.convert(input_path)
        output_name = input_path.stem + ".md"
        output_path = os.path.join(output_dir, output_name)
        markdown_content = result.document.export_to_markdown()
        
        # Save markdown locally
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        logging.info(f"✅ Saved markdown: {output_path}")
        
        # Upload to S3 if configured
        s3_key = None
        if s3_bucket and s3_prefix:
            s3_key = f"{s3_prefix}{Path(output_path).name}"
            upload_to_s3(output_path, s3_bucket, s3_key)
            
            # Upload images if any
            if os.path.isdir(images_dir):
                for img_file in os.listdir(images_dir):
                    img_path = os.path.join(images_dir, img_file)
                    if os.path.isfile(img_path):
                        upload_to_s3(img_path, s3_bucket, f"{s3_prefix}images/{img_file}")
        
        return s3_key or output_path
        
    except Exception as e:
        logging.error(f"Error processing XLSX file: {e}")
        raise

    def process_message(self, ch, method, properties, body):
        """Process incoming message from the queue."""
        try:
            payload = json.loads(body)
            logger.info(f"📩 Received message: {payload}")
            
            # Extract necessary information from payload
            input_path = payload.get('s3Key')
            filename = payload.get('filename', 'unknown')
            document_id = payload.get('documentId')
            s3_bucket = payload.get('s3Bucket') or os.getenv('S3_BUCKET_NAME', 'semantic-chunking-bucket')
            
            # Generate output path
            output_s3_prefix = f"parsed/{document_id}/"
            
            logger.info(f"🚀 Processing XLSX file: {filename}")
            
            # Call the parser function
            result = extract_xlsx_to_markdown(
                input_path=input_path,
                output_dir=output_s3_prefix,
                s3_bucket=s3_bucket,
                s3_prefix=output_s3_prefix
            )
            
            # Send result to chunking queue
            chunking_payload = {
                's3Bucket': s3_bucket,
                's3Key': result,
                'documentId': document_id,
                'fileType': 'xlsx'
            }
            
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
            
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}", exc_info=True)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def start_consuming(self):
        """Start consuming messages from the queue."""
        try:
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue='xlsx-parser-queue',
                on_message_callback=self.process_message,
                auto_ack=False
            )
            
            logger.info("🔄 Waiting for messages in xlsx-parser-queue...")
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("\n👋 Shutting down XLSX parser...")
            if self.connection:
                self.connection.close()


def main():
    parser = argparse.ArgumentParser(description='Run XLSX parser worker')
    parser.add_argument('--rabbitmq', type=str, 
                       default='amqp://admin:admin@52.65.216.159:5672',
                       help='RabbitMQ connection URL')
    
    args = parser.parse_args()
    
    # Create and start worker
    worker = XlsxParserService(args.rabbitmq)
    worker.connect()
    worker.start_consuming()

if __name__ == "__main__":
    main()
