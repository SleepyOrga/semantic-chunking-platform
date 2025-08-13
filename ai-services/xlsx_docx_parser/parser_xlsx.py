import os
import tempfile
import argparse
import boto3
import json
import pika
import logging
from pathlib import Path
import requests
import logging
import json
import pika
from typing import Dict, Any, Optional

import pandas as pd
from typing import List, Dict
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

    def process_message(self, ch, method, properties, body):
        """Process incoming message from the queue."""
        try:
            payload = json.loads(body)
            logger.info(f"📩 Received message: {payload}")
            
            # Extract necessary information from payload
            input_s3_key = payload.get('s3Key')
            filename = payload.get('filename', 'unknown')
            document_id = payload.get('documentId')
            s3_bucket = payload.get('s3Bucket') or os.getenv('AWS_S3_BUCKET_NAME', 'semantic-chunking-bucket')
            
            logger.info(f"🚀 Processing XLSX file: {filename} from s3://{s3_bucket}/{input_s3_key}")
            
            # Call the parser function - saves directly to S3
            result_s3_key = extract_xlsx_to_markdown(
                input_path=input_s3_key,
                output_dir=None,  # Not used when saving to S3
                s3_bucket=s3_bucket,
                s3_prefix=None  # We'll generate the key to match original file location
            )
            
            logger.info(f"✅ Processed XLSX file, result saved to s3://{s3_bucket}/{result_s3_key}")
            
            # Send result to chunking queue
            chunking_payload = {
                's3Bucket': s3_bucket,
                's3Key': result_s3_key,
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

def download_from_s3(s3_bucket, s3_key, local_path):
    """Download file from S3 to local path"""
    try:
        s3 = boto3.client('s3')
        s3.download_file(s3_bucket, s3_key, local_path)
        logging.info(f"Downloaded s3://{s3_bucket}/{s3_key} to {local_path}")
        return local_path
    except Exception as e:
        logging.error(f"Failed to download from S3: {e}")
        raise

def read_xlsx_and_convert(filepath: str) -> Dict[str, List[str]]:
    xls = pd.ExcelFile(filepath)
    result = {}

    for sheetname in xls.sheet_names:
        df = xls.parse(sheetname, header=None, dtype=str)
        df = df.fillna("")
        lines = []

        current_table = []
        current_text_block = []

        for _, row in df.iterrows():
            row_vals = [str(cell).strip() for cell in row if str(cell).strip()]
            if not row_vals:
                # End of a block
                if current_table:
                    lines.extend(convert_table_to_sentences(current_table))
                    current_table = []
                    lines.append("\n")  # Add a blank line to separate blocks
                    
                if current_text_block:
                    lines.append("\n".join(current_text_block))
                    lines.append("\n")  # Add a blank line to separate blocks
                    current_text_block = []
                continue

            if is_probably_table_row(row):
                # Flush text block if needed
                if current_text_block:
                    lines.append(" ".join(current_text_block))
                    current_text_block = []

                current_table.append(row.tolist())
            else:
                # Flush table block if needed
                if current_table:
                    lines.extend(convert_table_to_sentences(current_table))
                    current_table = []
                current_text_block.append("\n".join(row_vals))

        # Flush any remaining data
        if current_table:
            lines.extend(convert_table_to_sentences(current_table))
        if current_text_block:
            lines.append("\n".join(current_text_block))

        result[sheetname] = lines
    return result


def is_probably_table_row(row, min_non_empty=2) -> bool:
    """
    A row is likely part of a table if it has enough non-empty cells
    and is consistent with tabular layout.
    """
    cells = [str(cell).strip() for cell in row]
    non_empty = sum(1 for cell in cells if cell)
    return non_empty >= min_non_empty


def convert_table_to_sentences(table_rows: List[List[str]]) -> List[str]:
    if not table_rows or len(table_rows) < 2:
        return []

    # Assume first row is header
    header = [str(cell).strip() for cell in table_rows[0]]
    sentences = []

    for row in table_rows[1:]:
        cells = [str(cell).strip() for cell in row]
        parts = []
        for col, val in zip(header, cells):
            if col and val:
                parts.append(f"{col}: {val}")
        sentence = ". ".join(parts)
        if sentence:
            sentences.append(sentence)
    return sentences


def save_to_text_files(sheet_data: Dict[str, List[str]], output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        for sheetname, lines in sheet_data.items():
            f.write(f"# {sheetname}\n\n")
            for line in lines:
                f.write(line.strip() + "\n")
            f.write("\n")  # Add a blank line after each sheet
        
              
def extract_xlsx_to_markdown(input_path, output_dir=None, s3_bucket=None, s3_prefix=None, original_s3_key=None):
    """
    Extract XLSX to markdown.
    
    Args:
        input_path: File path to the XLSX file (when used by worker) or S3 key
        output_dir: Local directory to save output (when used by worker) or None for S3
        s3_bucket: S3 bucket name to save the output (optional)
        s3_prefix: S3 prefix for output files (optional)
        original_s3_key: Original S3 key for proper naming (optional)
        
    Returns:
        S3 key of the saved markdown file (if S3 mode) or local path (if local mode)
    """
    
    # Simple local mode for worker usage
    if output_dir and not s3_bucket:
        sheet_data = read_xlsx_and_convert(input_path)
        os.makedirs(output_dir, exist_ok=True)
        input_path = Path(input_path)
        output_name = input_path.stem + ".md"
        output_path = os.path.join(output_dir, output_name)
        save_to_text_files(sheet_data, output_path)
        return output_path
    
    # S3 mode for direct S3 processing
    return _extract_xlsx_to_markdown_s3(input_path, s3_bucket, s3_prefix, original_s3_key)  
def extract_xlsx_to_markdown_old(input_path, output_dir=None, s3_bucket=None, s3_prefix=None, original_s3_key=None):
    """
    Extract XLSX to markdown.
    
    Args:
        input_path: File path to the XLSX file (when used by worker) or S3 key
        output_dir: Local directory to save output (when used by worker) or None for S3
        s3_bucket: S3 bucket name to save the output (optional)
        s3_prefix: S3 prefix for output files (optional)
        original_s3_key: Original S3 key for proper naming (optional)
        
    Returns:
        S3 key of the saved markdown file (if S3 mode) or local path (if local mode)
    """
    
    # Simple local mode for worker usage
    if output_dir and not s3_bucket:
        return _extract_xlsx_to_markdown_local(input_path, output_dir)
    
    # S3 mode for direct S3 processing
    return _extract_xlsx_to_markdown_s3(input_path, s3_bucket, s3_prefix, original_s3_key)

def _extract_xlsx_to_markdown_local(input_path, output_dir):
    """Simple local extraction for worker usage"""
    try:
        import tempfile
        
        # Initialize the document converter
        converter = DocumentConverter(
            format_options={
                InputFormat.XLSX: ExcelFormatOption(
                    pipeline_cls=SimplePipeline,
                    backend=MsExcelDocumentBackend
                )
            }
        )
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Process the file
        input_path = Path(input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
            
        logging.info(f"Processing {input_path.name}")
        result = converter.convert(input_path)
        
        # Generate output filename
        output_name = input_path.stem + ".md"
        output_path = os.path.join(output_dir, output_name)
        
        # Export to markdown
        markdown_content = result.document.export_to_markdown()
        
        # Save markdown locally
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        logging.info(f"✅ Saved markdown: {output_path}")
        
        return output_path
        
    except Exception as e:
        logging.error(f"Error processing XLSX file: {e}")
        raise

def _extract_xlsx_to_markdown_s3(input_path, s3_bucket, s3_prefix=None, original_s3_key=None):
    """Extract XLSX to markdown and save directly to S3"""
    temp_input_file = None
    temp_output_file = None
    temp_images_dir = None
    
    try:
        import tempfile
        
        # Initialize the document converter
        converter = DocumentConverter(
            format_options={
                InputFormat.XLSX: ExcelFormatOption(
                    pipeline_cls=SimplePipeline,
                    backend=MsExcelDocumentBackend
                )
            }
        )
        
        # Handle input path (could be a file path, URL, or S3 key)
        local_path = input_path
        original_s3_key = input_path  # Store original S3 key for later use
        
        if isinstance(input_path, str):
            if input_path.startswith("http://") or input_path.startswith("https://"):
                # Handle HTTP/HTTPS URLs
                local_path = download_file_from_url(input_path)
                if not local_path:
                    raise Exception("Failed to download file from URL")
            elif s3_bucket and not os.path.exists(input_path):
                # Handle S3 keys - download to temporary file
                temp_input_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
                temp_input_file.close()
                local_path = download_from_s3(s3_bucket, input_path, temp_input_file.name)
        
        input_path = Path(local_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
            
        # Create temporary directory for images if needed
        temp_images_dir = tempfile.mkdtemp(prefix='xlsx_images_')
        
        # Process the file
        logging.info(f"Processing {input_path.name}")
        result = converter.convert(input_path)
        
        # Generate markdown content
        markdown_content = result.document.export_to_markdown()
        
        # Create temporary file for markdown output
        temp_output_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md', encoding='utf-8')
        temp_output_file.write(markdown_content)
        temp_output_file.close()
        
        logging.info(f"✅ Generated markdown content")
        
        # Upload markdown to S3
        if not s3_bucket:
            raise ValueError("s3_bucket is required for S3 upload")
            
        # Generate S3 key for markdown file by replacing extension like PDF parser does
        if s3_prefix:
            # If s3_prefix is provided, use the old logic
            original_name = input_path.stem
            markdown_s3_key = f"{s3_prefix}{original_name}.md"
        elif original_s3_key:
            # Generate key by replacing extension of original S3 key (like PDF parser)
            if '.' in original_s3_key:
                markdown_s3_key = '.'.join(original_s3_key.split('.')[:-1]) + '.md'
            else:
                markdown_s3_key = original_s3_key + '.md'
        else:
            # Fallback: use filename with .md extension
            original_name = input_path.stem
            markdown_s3_key = f"{original_name}.md"
        
        # Upload markdown file to S3
        upload_to_s3(temp_output_file.name, s3_bucket, markdown_s3_key)
        logging.info(f"✅ Uploaded markdown to s3://{s3_bucket}/{markdown_s3_key}")
        
        # Upload images if any were generated
        if os.path.isdir(temp_images_dir) and os.listdir(temp_images_dir):
            for img_file in os.listdir(temp_images_dir):
                img_path = os.path.join(temp_images_dir, img_file)
                if os.path.isfile(img_path):
                    img_s3_key = f"{s3_prefix}images/{img_file}" if s3_prefix else f"images/{img_file}"
                    upload_to_s3(img_path, s3_bucket, img_s3_key)
                    logging.info(f"Uploaded image to s3://{s3_bucket}/{img_s3_key}")
        
        return markdown_s3_key
        
    except Exception as e:
        logging.error(f"Error processing XLSX file: {e}")
        raise
    finally:
        # Clean up all temporary files and directories
        if temp_input_file and os.path.exists(temp_input_file.name):
            try:
                os.unlink(temp_input_file.name)
                logging.info(f"Cleaned up temporary input file: {temp_input_file.name}")
            except Exception as e:
                logging.warning(f"Failed to delete temporary input file: {e}")
        
        if temp_output_file and os.path.exists(temp_output_file.name):
            try:
                os.unlink(temp_output_file.name)
                logging.info(f"Cleaned up temporary output file: {temp_output_file.name}")
            except Exception as e:
                logging.warning(f"Failed to delete temporary output file: {e}")
        
        if temp_images_dir and os.path.exists(temp_images_dir):
            try:
                import shutil
                shutil.rmtree(temp_images_dir)
                logging.info(f"Cleaned up temporary images directory: {temp_images_dir}")
            except Exception as e:
                logging.warning(f"Failed to delete temporary images directory: {e}")


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
