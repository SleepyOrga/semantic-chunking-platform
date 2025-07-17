import pika
import boto3
import tempfile
import subprocess
import json
import os
import sys
import traceback
import psycopg2

# ✅ Địa chỉ RabbitMQ server mặc định dùng remote IP
RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://admin:admin@52.65.216.159:5672/")
QUEUE_NAME = "chunking-queue"
CHUNKER_SCRIPT = os.environ.get("CHUNKER_SCRIPT", "chunking_agent.py")
AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-2")

# PostgreSQL connection from environment
PG_HOST = os.environ.get("PG_HOST", "localhost")
PG_PORT = os.environ.get("PG_PORT", "5433")
PG_USER = os.environ.get("PG_USER", "app_user")
PG_PASSWORD = os.environ.get("PG_PASSWORD", "secret123")
PG_DB = os.environ.get("PG_DB", "app_db")

s3 = boto3.client("s3", region_name=AWS_REGION)

def insert_chunks_to_postgres(document_id, chunks):
    print(f"[DEBUG] Inserting {len(chunks)} chunks into PostgreSQL for document {document_id}")
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            dbname=PG_DB
        )
        cur = conn.cursor()
        for idx, chunk in enumerate(chunks):
            cur.execute(
                """
                INSERT INTO chunks (document_id, chunk_index, content, embedding, tag_embedding)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (document_id, chunk_index) DO NOTHING
                """,
                (
                    document_id,
                    idx,
                    chunk.get('content', ''),
                    None,  # embedding
                    None   # tag_embedding
                )
            )
        conn.commit()
        cur.close()
        conn.close()
        print(f"[DEBUG] Inserted {len(chunks)} chunks into PostgreSQL for document {document_id}")
    except Exception as e:
        print(f"[ERROR] Failed to insert chunks into PostgreSQL: {e}")
        traceback.print_exc()

def process_chunking_job(job):
    print(f"[DEBUG] Processing job: {job}")
    s3_bucket = job['s3Bucket']
    s3_key = job['s3Key']
    document_id = job['documentId']
    file_type = job.get('fileType', 'docx')

    # Download markdown from S3
    try:
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as tmp_md:
            print(f"[DEBUG] Downloading {s3_key} from S3 bucket {s3_bucket} to {tmp_md.name}")
            s3.download_fileobj(s3_bucket, s3_key, tmp_md)
            tmp_md_path = tmp_md.name
    except Exception as e:
        print(f"[ERROR] Failed to download from S3: {e}")
        traceback.print_exc()
        raise

    # Run chunking agent
    output_json = f"{tmp_md_path}.chunks.json"
    try:
        print(f"[DEBUG] Running chunking agent: {CHUNKER_SCRIPT} {tmp_md_path} --output_file {output_json}")
        result = subprocess.run([
            sys.executable, CHUNKER_SCRIPT,
            tmp_md_path,
            "--output_file", output_json
        ], check=True, capture_output=True, text=True)
        print(f"[DEBUG] Chunking agent stdout:\n{result.stdout}")
        print(f"[DEBUG] Chunking agent stderr:\n{result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Chunking agent failed: {e}")
        print(f"[ERROR] stdout:\n{e.stdout}")
        print(f"[ERROR] stderr:\n{e.stderr}")
        traceback.print_exc()
        raise

    # Upload result to S3
    result_s3_key = s3_key.replace('.md', '.chunks.json')
    try:
        print(f"[DEBUG] Uploading {output_json} to s3://{s3_bucket}/{result_s3_key}")
        s3.upload_file(output_json, s3_bucket, result_s3_key)
        print(f"[DEBUG] Uploaded chunks to s3://{s3_bucket}/{result_s3_key}")
    except Exception as e:
        print(f"[ERROR] Failed to upload to S3: {e}")
        traceback.print_exc()
        raise

    # Insert chunks into PostgreSQL
    try:
        with open(output_json, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        insert_chunks_to_postgres(document_id, chunks)
    except Exception as e:
        print(f"[ERROR] Failed to insert chunks into PostgreSQL: {e}")
        traceback.print_exc()

    # Clean up temp files
    try:
        os.remove(tmp_md_path)
        os.remove(output_json)
        print(f"[DEBUG] Cleaned up temp files: {tmp_md_path}, {output_json}")
    except Exception as e:
        print(f"[WARN] Failed to clean up temp files: {e}")
        traceback.print_exc()

def callback(ch, method, properties, body):
    print(" [x] Callback triggered!")
    print(" [x] Raw body:", body)
    try:
        job = json.loads(body)
        print(f"[DEBUG] Parsed job: {job}")
        process_chunking_job(job)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print("[DEBUG] Job processed and acknowledged.")
    except Exception as e:
        print(f"[ERROR] Error processing job: {e}")
        traceback.print_exc()
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def main():
    print(f"[DEBUG] Connecting to RabbitMQ at {RABBITMQ_URL}")
    try:
        params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
    except Exception as conn_err:
        print(f"[FATAL] Could not connect to RabbitMQ: {conn_err}")
        traceback.print_exc()
        return

    channel = connection.channel()
    print(f"[DEBUG] Declaring queue: {QUEUE_NAME}")
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    # Prefetch để xử lý từng job một
    channel.basic_qos(prefetch_count=1)

    print(f"[DEBUG] Starting to consume from queue: {QUEUE_NAME}")
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

    print(" [*] Waiting for chunking jobs. To exit press CTRL+C")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print(" [x] KeyboardInterrupt: Stopping consumer...")
        channel.stop_consuming()
    finally:
        connection.close()
        print(" [x] Connection closed.")

if __name__ == "__main__":
    main()
