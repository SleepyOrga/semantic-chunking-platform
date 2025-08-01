import pika
import boto3
import tempfile
import json
import os
import sys
import traceback
from dotenv import load_dotenv
from parser_xlsx import extract_xlsx_to_markdown
import pandas as pd
from typing import List, Dict
load_dotenv()

# Configuration
RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://admin:admin@52.65.216.159:5672/")
XLSX_PARSER_QUEUE = "xlsx-parser-queue"
CHUNKING_QUEUE = "chunking-queue"
AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
S3_BUCKET = os.environ.get("AWS_S3_BUCKET_NAME", "semantic-chunking-bucket")

s3 = boto3.client("s3", region_name=AWS_REGION)

def process_xlsx_message(message):
    """Process XLSX file from message"""
    print(f"[DEBUG] Processing XLSX message: {message}")
    
    s3_key = message['s3Key']
    document_id = message['documentId']
    filename = message['filename']
    s3_bucket = message.get('s3Bucket', S3_BUCKET)  # Use from message or fallback to env var
    
    # Download XLSX from S3
    tmp_xlsx_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_xlsx:
            print(f"[DEBUG] Downloading {s3_key} from S3 to {tmp_xlsx.name}")
            s3.download_fileobj(s3_bucket, s3_key, tmp_xlsx)
            tmp_xlsx_path = tmp_xlsx.name
    except Exception as e:
        print(f"[ERROR] Failed to download XLSX from S3: {e}")
        raise
    
    # Convert XLSX to Markdown
    try:
        print(f"[DEBUG] Converting XLSX to Markdown: {tmp_xlsx_path}")
        
        # Use a simple temporary directory approach like DOCX worker
        with tempfile.TemporaryDirectory() as temp_output_dir:
            # Call extract_xlsx_to_markdown - simplified version
            extract_xlsx_to_markdown(tmp_xlsx_path, temp_output_dir)
            
            # Find the generated markdown file
            xlsx_stem = os.path.splitext(os.path.basename(tmp_xlsx_path))[0]
            markdown_file = os.path.join(temp_output_dir, f"{xlsx_stem}.md")
            
            if os.path.exists(markdown_file):
                with open(markdown_file, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
            else:
                raise Exception(f"Markdown file not found at {markdown_file}")
        
        # Save markdown to temp file for upload
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as tmp_md:
            tmp_md.write(markdown_content)
            tmp_md_path = tmp_md.name
            
    except Exception as e:
        print(f"[ERROR] Failed to convert XLSX to Markdown: {e}")
        raise
    
    # Upload Markdown to S3 (same approach as DOCX worker)
    try:
        # Generate markdown S3 key by replacing extension like DOCX worker does
        markdown_s3_key = s3_key.replace('.xlsx', '.md')
        print(f"[DEBUG] Uploading markdown to s3://{s3_bucket}/{markdown_s3_key}")
        s3.upload_file(tmp_md_path, s3_bucket, markdown_s3_key)
        print(f"[DEBUG] Markdown uploaded successfully")
    except Exception as e:
        print(f"[ERROR] Failed to upload markdown to S3: {e}")
        raise
    
    # Prepare chunking message
    try:
        chunking_message = {
            "documentId": document_id,
            "s3Bucket": s3_bucket,
            "s3Key": markdown_s3_key,
            "fileType": "xlsx",
            "originalFilename": filename
        }
        
        return chunking_message
        
    except Exception as e:
        print(f"[ERROR] Failed to prepare chunking message: {e}")
        raise
    finally:
        # Cleanup temp files
        try:
            if tmp_xlsx_path:
                os.unlink(tmp_xlsx_path)
            if 'tmp_md_path' in locals():
                os.unlink(tmp_md_path)
        except Exception as cleanup_error:
            print(f"[WARN] Failed to cleanup temp files: {cleanup_error}")

def send_to_chunking_queue(channel, message):
    """Send processed document to chunking queue"""
    try:
        channel.queue_declare(queue=CHUNKING_QUEUE, durable=True)
        channel.basic_publish(
            exchange='',
            routing_key=CHUNKING_QUEUE,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                content_type='application/json',
                delivery_mode=2  # persistent
            )
        )
        
        print(f"[DEBUG] Sent document {message['documentId']} to chunking queue")
        
    except Exception as e:
        print(f"[ERROR] Failed to send to chunking queue: {e}")
        raise

def callback(ch, method, properties, body):
    print(f"[DEBUG] XLSX Parser received message")
    try:
        message = json.loads(body)
        print(f"[DEBUG] Parsed message: {message}")
        
        chunking_message = process_xlsx_message(message)
        send_to_chunking_queue(ch, chunking_message)
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"[DEBUG] XLSX processing completed and acknowledged")
        
    except Exception as e:
        print(f"[ERROR] Error processing XLSX message: {e}")
        traceback.print_exc()
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def main():
    print(f"[DEBUG] XLSX Parser connecting to RabbitMQ at {RABBITMQ_URL}")
    try:
        params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
    except Exception as conn_err:
        print(f"[FATAL] Could not connect to RabbitMQ: {conn_err}")
        return

    channel = connection.channel()
    print(f"[DEBUG] Declaring queue: {XLSX_PARSER_QUEUE}")
    channel.queue_declare(queue=XLSX_PARSER_QUEUE, durable=True)

    # Prefetch one message at a time
    channel.basic_qos(prefetch_count=1)

    print(f"[DEBUG] Starting to consume from queue: {XLSX_PARSER_QUEUE}")
    channel.basic_consume(queue=XLSX_PARSER_QUEUE, on_message_callback=callback)

    print(" [*] XLSX Parser waiting for messages. To exit press CTRL+C")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print(" [x] KeyboardInterrupt: Stopping XLSX parser...")
        channel.stop_consuming()
    finally:
        connection.close()

if __name__ == "__main__":
    main()