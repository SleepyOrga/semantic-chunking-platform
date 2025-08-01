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
        
        # Create a temporary directory for output
        with tempfile.TemporaryDirectory() as temp_output_dir:
            # Use extract_xlsx_to_markdown with S3 params like DOCX worker
            s3_prefix = f"parsed/{document_id}/"
            markdown_s3_key = extract_xlsx_to_markdown(
                input_path=tmp_xlsx_path,
                output_dir=temp_output_dir,
                s3_bucket=s3_bucket,
                s3_prefix=s3_prefix
            )
            
            print(f"[DEBUG] Markdown uploaded to S3: {markdown_s3_key}")
            
    except Exception as e:
        print(f"[ERROR] Failed to convert XLSX to Markdown: {e}")
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