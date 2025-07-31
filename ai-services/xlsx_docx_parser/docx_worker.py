import pika
import boto3
import tempfile
import json
import os
import sys
import traceback
from dotenv import load_dotenv
from parser_docx import extract_docx_to_markdown

load_dotenv()

# Configuration
RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://admin:admin@52.65.216.159:5672/")
DOCX_PARSER_QUEUE = "docx-parser-queue"
CHUNKING_QUEUE = "chunking-queue"
AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
S3_BUCKET = os.environ.get("AWS_S3_BUCKET_NAME", "semantic-chunking-bucket")

s3 = boto3.client("s3", region_name=AWS_REGION)

def process_docx_message(message):
    """Process DOCX file from message"""
    print(f"[DEBUG] Processing DOCX message: {message}")
    
    s3_key = message['s3Key']
    document_id = message['documentId']
    filename = message['filename']
    
    # Download DOCX from S3
    try:
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_docx:
            print(f"[DEBUG] Downloading {s3_key} from S3 to {tmp_docx.name}")
            s3.download_fileobj(S3_BUCKET, s3_key, tmp_docx)
            tmp_docx_path = tmp_docx.name
    except Exception as e:
        print(f"[ERROR] Failed to download DOCX from S3: {e}")
        raise
    
    # Convert DOCX to Markdown
    try:
        print(f"[DEBUG] Converting DOCX to Markdown: {tmp_docx_path}")
        
        # Create a temporary directory for output
        with tempfile.TemporaryDirectory() as temp_output_dir:
            # Use the extract_docx_to_markdown function
            s3_prefix = f"parsed/{document_id}/"
            # extract_docx_to_markdown(tmp_docx_path, temp_output_dir, extract_images=True)
            
            # # Find the generated markdown file
            # docx_stem = os.path.splitext(os.path.basename(tmp_docx_path))[0]
            # markdown_file = os.path.join(temp_output_dir, f"{docx_stem}.md")

            markdown_s3_key = extract_docx_to_markdown(
                input_path=tmp_docx_path,
                output_dir=temp_output_dir,
                extract_images=True,
                s3_bucket=S3_BUCKET,       
                s3_prefix=s3_prefix        
            )
            
            print(f"[DEBUG] Markdown uploaded to S3: {markdown_s3_key}")
        #     if os.path.exists(markdown_file):
        #         with open(markdown_file, 'r', encoding='utf-8') as f:
        #             markdown_content = f.read()
        #     else:
        #         raise Exception(f"Markdown file not found at {markdown_file}")
        
        # # Save markdown to temp file for upload
        # with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as tmp_md:
        #     tmp_md.write(markdown_content)
        #     tmp_md_path = tmp_md.name
            
    except Exception as e:
        print(f"[ERROR] Failed to convert DOCX to Markdown: {e}")
        raise
    
    # # Upload Markdown to S3
    # try:
    #     markdown_s3_key = s3_key.replace('.docx', '.md')
    #     print(f"[DEBUG] Uploading markdown to s3://{S3_BUCKET}/{markdown_s3_key}")
    #     s3.upload_file(tmp_md_path, S3_BUCKET, markdown_s3_key)
    #     print(f"[DEBUG] Markdown uploaded successfully")
    # except Exception as e:
    #     print(f"[ERROR] Failed to upload markdown to S3: {e}")
    #     raise
    
    # Send to chunking queue
    try:
        chunking_message = {
            "documentId": document_id,
            "s3Bucket": S3_BUCKET,
            "s3Key": markdown_s3_key,
            "fileType": "docx",
            "originalFilename": filename
        }
        
        return chunking_message
        
    except Exception as e:
        print(f"[ERROR] Failed to prepare chunking message: {e}")
        raise
    finally:
        # Cleanup temp files
        try:
            os.remove(tmp_docx_path)
            #os.remove(tmp_md_path)
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
    print(f"[DEBUG] DOCX Parser received message")
    try:
        message = json.loads(body)
        print(f"[DEBUG] Parsed message: {message}")
        
        chunking_message = process_docx_message(message)
        send_to_chunking_queue(ch, chunking_message)
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"[DEBUG] DOCX processing completed and acknowledged")
        
    except Exception as e:
        print(f"[ERROR] Error processing DOCX message: {e}")
        traceback.print_exc()
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def main():
    print(f"[DEBUG] DOCX Parser connecting to RabbitMQ at {RABBITMQ_URL}")
    try:
        params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
    except Exception as conn_err:
        print(f"[FATAL] Could not connect to RabbitMQ: {conn_err}")
        return

    channel = connection.channel()
    print(f"[DEBUG] Declaring queue: {DOCX_PARSER_QUEUE}")
    channel.queue_declare(queue=DOCX_PARSER_QUEUE, durable=True)

    # Prefetch one message at a time
    channel.basic_qos(prefetch_count=1)

    print(f"[DEBUG] Starting to consume from queue: {DOCX_PARSER_QUEUE}")
    channel.basic_consume(queue=DOCX_PARSER_QUEUE, on_message_callback=callback)

    print(" [*] DOCX Parser waiting for messages. To exit press CTRL+C")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print(" [x] KeyboardInterrupt: Stopping DOCX parser...")
        channel.stop_consuming()
    finally:
        connection.close()

if __name__ == "__main__":
    main()