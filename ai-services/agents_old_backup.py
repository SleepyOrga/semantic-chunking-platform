import asyncio
import json
import pika
from pika.adapters.asyncio_connection import AsyncioConnection
import os
import sys
import aioboto3
import aiofiles
from dotenv import load_dotenv

load_dotenv()

# --- Configuration (from environment variables) ---
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', '52.65.216.159')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'admin')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'admin')
AMQP_URL = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"

AWS_S3_BUCKET_NAME = os.getenv('AWS_S3_BUCKET_NAME', 'semantic-chunking-bucket')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

INPUT_QUEUE = 'file-process-queue'
OUTPUT_QUEUE = 'file-loaded-queue'

MAX_CONCURRENT_DOWNLOADS = 10

class AsyncS3Consumer:
    def __init__(self):
        self._connection = None
        self._channel = None
        self._s3_client = None
        self._download_semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
        os.makedirs('temp', exist_ok=True)
        os.makedirs('save_dir', exist_ok=True)

    async def connect_and_setup(self):
        """Establishes connections to RabbitMQ and S3."""
        print("Connecting to RabbitMQ...")
        self._connection = await AsyncioConnection(pika.URLParameters(AMQP_URL))
        self._channel = await self._connection.channel()
        print("Successfully connected to RabbitMQ.")

        print("Setting up S3 client...")
        session = aioboto3.Session(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        self._s3_client = session.client('s3')
        print("S3 client is ready.")

        # Declare queues
        await self._channel.queue_declare(queue=INPUT_QUEUE, durable=True)
        await self._channel.queue_declare(queue=OUTPUT_QUEUE, durable=True)
        
        # Set Quality of Service
        await self._channel.basic_qos(prefetch_count=MAX_CONCURRENT_DOWNLOADS)

    async def download_s3_file(self, key, local_path):
        """Asynchronously downloads a file from S3 and saves it."""
        try:
            print(f"Downloading s3://{AWS_S3_BUCKET_NAME}/{key}...")
            response = await self._s3_client.get_object(Bucket=AWS_S3_BUCKET_NAME, Key=key)
            
            async with response['Body'] as stream:
                file_content = await stream.read()

            async with aiofiles.open(local_path, 'wb') as local_file:
                await local_file.write(file_content)
            
            print(f"File saved locally at {local_path}")
            return local_path
        except Exception as e:
            print(f"Error downloading file from S3: {e}", file=sys.stderr)
            return None

    def on_message(self, channel, method, properties, body):
        """
        Synchronous callback from Pika.
        It schedules the asynchronous processing of the message.
        """
        print(f" [x] Received message with delivery_tag {method.delivery_tag}")
        # Schedule the async processing of the message without blocking the callback
        asyncio.create_task(self.process_message(body, method.delivery_tag))

    async def process_message(self, body, delivery_tag):
        """Asynchronously processes a single message."""
        async with self._download_semaphore:
            try:
                message_data = json.loads(body.decode('utf-8'))
                key = message_data['s3Key']
                
                filename, save_name, ext = key.split('/')[-1].rsplit('.', 2)
                local_file_path = f'temp/{save_name}'

                # Await the async download
                saved_file_path = await self.download_s3_file(key, local_file_path)

                if saved_file_path:
                    # Prepare the new message
                    output_message = {
                        'filename': filename,
                        'save_name': save_name,
                        'ext': ext,
                        'saved_file_path': saved_file_path
                    }

                    # Await the async publish
                    await self._channel.basic_publish(
                        exchange='',
                        routing_key=OUTPUT_QUEUE,
                        body=json.dumps(output_message).encode('utf-8'),
                        properties=pika.BasicProperties(
                            content_type='application/json',
                            delivery_mode=pika.DeliveryMode.Persistent
                        )
                    )
                    print(f" [+] Published processed message to '{OUTPUT_QUEUE}'")

                # Acknowledge the original message
                await self._channel.basic_ack(delivery_tag)
                print(f" [✓] Acknowledged message {delivery_tag}")

            except Exception as e:
                print(f" [!] Error processing message {delivery_tag}: {e}", file=sys.stderr)
                # Optionally, reject the message so it can be re-queued or sent to a dead-letter exchange
                await self._channel.basic_nack(delivery_tag, requeue=False)

    async def run(self):
        """Main execution loop."""
        await self.connect_and_setup()
        await self._channel.basic_consume(INPUT_QUEUE, self.on_message)
        print(f"[*] Waiting for messages on queue '{INPUT_QUEUE}'. To exit press CTRL+C")
        try:
            # Wait forever
            await asyncio.Future()
        finally:
            print("Closing connections...")
            if self._s3_client:
                await self._s3_client.close()
            if self._connection and not self._connection.is_closed:
                await self._connection.close()

async def main():
    consumer = AsyncS3Consumer()
    await consumer.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted by user. Shutting down.")