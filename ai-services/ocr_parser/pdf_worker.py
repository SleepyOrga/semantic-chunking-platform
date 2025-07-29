import pika
import boto3
import tempfile
import subprocess
import json
import os
import sys
import traceback
from dotenv import load_dotenv

# Import OCR processing functions directly from main.py
from main import DOLPHINClient, process_document

load_dotenv()

# Configuration
RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://admin:admin@52.65.216.159:5672/")
PDF_PARSER_QUEUE = "pdf-parser-queue"
CHUNKING_QUEUE = "chunking-queue"
AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
S3_BUCKET = os.environ.get("AWS_S3_BUCKET_NAME", "semantic-chunking-bucket")

# RabbitMQ connection parameters with longer heartbeat for long-running operations
HEARTBEAT_TIMEOUT = 300  # 5 minutes
BLOCKED_CONNECTION_TIMEOUT = 300  # 5 minutes

s3 = boto3.client("s3", region_name=AWS_REGION)

# Global publisher connection for sending results
publisher_connection = None
publisher_channel = None

def get_publisher_connection():
    """Get or create a dedicated publisher connection"""
    global publisher_connection, publisher_channel
    
    try:
        # Check if connection exists and is open
        if publisher_connection and not publisher_connection.is_closed:
            return publisher_connection, publisher_channel
    except:
        pass
    
    # Create new connection
    try:
        params = pika.URLParameters(RABBITMQ_URL)
        params.heartbeat = HEARTBEAT_TIMEOUT
        params.blocked_connection_timeout = BLOCKED_CONNECTION_TIMEOUT
        
        publisher_connection = pika.BlockingConnection(params)
        publisher_channel = publisher_connection.channel()
        publisher_channel.queue_declare(queue=CHUNKING_QUEUE, durable=True)
        
        print("[DEBUG] Created new publisher connection")
        return publisher_connection, publisher_channel
    except Exception as e:
        print(f"[ERROR] Failed to create publisher connection: {e}")
        raise

def close_publisher_connection():
    """Close the publisher connection"""
    global publisher_connection
    if publisher_connection and not publisher_connection.is_closed:
        try:
            publisher_connection.close()
            print("[DEBUG] Closed publisher connection")
        except:
            pass

def process_pdf_message(message):
    """Process PDF/Image file from message"""
    print(f"[DEBUG] Processing PDF/Image message: {message}")
    
    s3_key = message['s3Key']
    document_id = message['documentId']
    filename = message['filename']
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
    
    # Download file from S3
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_file:
            print(f"[DEBUG] Downloading {s3_key} from S3 to {tmp_file.name}")
            s3.download_fileobj(S3_BUCKET, s3_key, tmp_file)
            tmp_file_path = tmp_file.name
    except Exception as e:
        print(f"[ERROR] Failed to download file from S3: {e}")
        raise
    
    # Process with OCR/PDF parser
    try:
        print(f"[DEBUG] Processing {file_type} file with OCR: {tmp_file_path}")
        
        # Create a temporary output directory
        with tempfile.TemporaryDirectory() as temp_output_dir:
            # Initialize the DOLPHIN model
            model = DOLPHINClient()
            
            # Process the document directly using the imported function
            print(f"[DEBUG] Processing document with OCR using direct function call")
            json_path, results = process_document(tmp_file_path, model, temp_output_dir)
            
            # The process_document function should have created a markdown file
            # Look for the markdown file in the expected location
            file_stem = os.path.splitext(os.path.basename(tmp_file_path))[0]
            markdown_path = os.path.join(temp_output_dir, "markdown", f"{file_stem}.md")
            
            if os.path.exists(markdown_path):
                with open(markdown_path, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
                print(f"[DEBUG] Successfully read markdown from: {markdown_path}")
            else:
                # Fallback: look for any .md file in the markdown directory
                markdown_dir = os.path.join(temp_output_dir, "markdown")
                if os.path.exists(markdown_dir):
                    md_files = [f for f in os.listdir(markdown_dir) if f.endswith('.md')]
                    if md_files:
                        markdown_path = os.path.join(markdown_dir, md_files[0])
                        with open(markdown_path, 'r', encoding='utf-8') as f:
                            markdown_content = f.read()
                        print(f"[DEBUG] Found and read markdown from: {markdown_path}")
                    else:
                        raise Exception("No markdown file generated by OCR processor")
                else:
                    raise Exception("No markdown directory created by OCR processor")
            
    except Exception as e:
        print(f"[ERROR] Failed to process file with OCR: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise
    
    # Save markdown content to temp file
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as tmp_md:
            tmp_md.write(markdown_content)
            tmp_md_path = tmp_md.name
    except Exception as e:
        print(f"[ERROR] Failed to save markdown content: {e}")
        raise
    
    # Upload Markdown to S3
    try:
        # Replace original extension with .md
        if '.' in s3_key:
            markdown_s3_key = '.'.join(s3_key.split('.')[:-1]) + '.md'
        else:
            markdown_s3_key = s3_key + '.md'
            
        print(f"[DEBUG] Uploading markdown to s3://{S3_BUCKET}/{markdown_s3_key}")
        s3.upload_file(tmp_md_path, S3_BUCKET, markdown_s3_key)
        print(f"[DEBUG] Markdown uploaded successfully")
    except Exception as e:
        print(f"[ERROR] Failed to upload markdown to S3: {e}")
        raise
    
    # Send to chunking queue
    try:
        chunking_message = {
            "documentId": document_id,
            "s3Bucket": S3_BUCKET,
            "s3Key": markdown_s3_key,
            "fileType": file_type,
            "originalFilename": filename
        }
        
        return chunking_message
        
    except Exception as e:
        print(f"[ERROR] Failed to prepare chunking message: {e}")
        raise
    finally:
        # Cleanup temp files
        try:
            os.remove(tmp_file_path)
            os.remove(tmp_md_path)
            # The OCR temp directory is cleaned up automatically by the context manager
        except Exception as cleanup_error:
            print(f"[WARN] Failed to cleanup temp files: {cleanup_error}")

def send_to_chunking_queue(message):
    """Send processed document to chunking queue using dedicated publisher connection"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Get dedicated publisher connection
            _, pub_channel = get_publisher_connection()
            
            pub_channel.basic_publish(
                exchange='',
                routing_key=CHUNKING_QUEUE,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    content_type='application/json',
                    delivery_mode=2  # persistent
                )
            )
            
            print(f"[DEBUG] Sent document {message['documentId']} to chunking queue")
            return  # Success, exit function
            
        except Exception as e:
            retry_count += 1
            print(f"[ERROR] Failed to send to chunking queue (attempt {retry_count}/{max_retries}): {e}")
            
            if retry_count < max_retries:
                print("[DEBUG] Retrying with new publisher connection...")
                # Force recreation of publisher connection on next attempt
                global publisher_connection
                if publisher_connection:
                    try:
                        publisher_connection.close()
                    except:
                        pass
                    publisher_connection = None
            else:
                raise

def callback(ch, method, properties, body):
    print(f"[DEBUG] PDF/OCR Parser received message")
    try:
        message = json.loads(body)
        print(f"[DEBUG] Parsed message: {message}")
        
        chunking_message = process_pdf_message(message)
        send_to_chunking_queue(chunking_message)  # No longer need to pass channel
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"[DEBUG] PDF/OCR processing completed and acknowledged")
        
    except Exception as e:
        print(f"[ERROR] Error processing PDF/OCR message: {e}")
        traceback.print_exc()
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def main():
    print(f"[DEBUG] PDF/OCR Parser connecting to RabbitMQ at {RABBITMQ_URL}")
    try:
        params = pika.URLParameters(RABBITMQ_URL)
        params.heartbeat = HEARTBEAT_TIMEOUT
        params.blocked_connection_timeout = BLOCKED_CONNECTION_TIMEOUT
        
        connection = pika.BlockingConnection(params)
        print(f"[DEBUG] Connected with heartbeat timeout: {HEARTBEAT_TIMEOUT}s")
    except Exception as conn_err:
        print(f"[FATAL] Could not connect to RabbitMQ: {conn_err}")
        return

    channel = connection.channel()
    print(f"[DEBUG] Declaring queue: {PDF_PARSER_QUEUE}")
    channel.queue_declare(queue=PDF_PARSER_QUEUE, durable=True)

    # Prefetch one message at a time to avoid overwhelming the worker during long processing
    channel.basic_qos(prefetch_count=1)

    print(f"[DEBUG] Starting to consume from queue: {PDF_PARSER_QUEUE}")
    channel.basic_consume(queue=PDF_PARSER_QUEUE, on_message_callback=callback)

    print(" [*] PDF/OCR Parser waiting for messages. To exit press CTRL+C")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print(" [x] KeyboardInterrupt: Stopping PDF/OCR parser...")
        channel.stop_consuming()
    finally:
        # Cleanup connections
        print("[DEBUG] Cleaning up connections...")
        close_publisher_connection()
        if connection and not connection.is_closed:
            connection.close()
        print("[DEBUG] Shutdown complete")

if __name__ == "__main__":
    main()