import asyncio
import json
import os
import sys
import boto3
import aio_pika
from dotenv import load_dotenv
from typing import List

load_dotenv()

# RabbitMQ config
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "admin")
AMQP_URL = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"

# SageMaker config
SAGEMAKER_ENDPOINT = os.getenv("SAGEMAKER_EMBEDDING_ENDPOINT")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Queue config
INPUT_QUEUE = "embedding-input-queue"
OUTPUT_QUEUE = "embedding-output-queue"

# Batch and concurrency config
BATCH_SIZE = 8
BATCH_TIMEOUT = 1  # seconds
MAX_CONCURRENT_BATCHES = 3  # limit SageMaker parallel requests

class BatchEmbedder:
    def __init__(self, sagemaker_endpoint: str, region: str, channel, semaphore: asyncio.Semaphore):
        self.endpoint = sagemaker_endpoint
        self.region = region
        self.channel = channel
        self.semaphore = semaphore

        self.sagemaker_runtime = boto3.client("sagemaker-runtime", region_name=self.region)
        self.pending_messages = []
        self.pending_texts = []
        self.batch_timer = None

    async def handle_message(self, message: aio_pika.IncomingMessage):
        async with message.process(ignore_processed=True):
            try:
                data = json.loads(message.body.decode())
                idx = data.get("chunk_id")
                text = data.get("content")

                if not text:
                    print("[!] Skipping message: no 'text' field")
                    await message.ack()
                    return

                self.pending_messages.append((message, data))
                self.pending_texts.append(text)

                if len(self.pending_messages) >= BATCH_SIZE:
                    await self._cancel_timer()
                    asyncio.create_task(self.process_batch())

                elif self.batch_timer is None:
                    loop = asyncio.get_event_loop()
                    self.batch_timer = loop.call_later(
                        BATCH_TIMEOUT,
                        lambda: asyncio.create_task(self.process_batch())
                    )

            except Exception as e:
                print(f"[!] Error handling message: {e}", file=sys.stderr)
                await message.nack(requeue=False)

    async def process_batch(self):
        if not self.pending_messages:
            return

        await self._cancel_timer()
        batch_size = len(self.pending_texts)
        print(f"[>] Processing batch of size {batch_size}")

        async with self.semaphore:
            try:
                embeddings = await self._call_sagemaker(self.pending_texts)

                if not isinstance(embeddings, list) or len(embeddings) != batch_size:
                    raise ValueError("SageMaker returned invalid or mismatched number of embeddings")

                for (message, original_data), embedding in zip(self.pending_messages, embeddings):
                    original_data["embedding"] = embedding

                    await self.channel.default_exchange.publish(
                        aio_pika.Message(
                            body=json.dumps(original_data).encode(),
                            content_type="application/json",
                            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                        ),
                        routing_key=OUTPUT_QUEUE,
                    )
                    await message.ack()

                print(f"[✓] Sent {batch_size} embeddings to '{OUTPUT_QUEUE}'")

            except Exception as e:
                print(f"[!] Failed to process batch: {e}", file=sys.stderr)
                for message, _ in self.pending_messages:
                    await message.nack(requeue=False)

            finally:
                self.pending_messages.clear()
                self.pending_texts.clear()

    async def _cancel_timer(self):
        if self.batch_timer:
            self.batch_timer.cancel()
            self.batch_timer = None

    async def _call_sagemaker(self, texts: List[str]) -> List[List[float]]:
        payload = json.dumps({"inputs": texts})
        response = self.sagemaker_runtime.invoke_endpoint(
            EndpointName=self.endpoint,
            ContentType="application/json",
            Body=payload,
        )
        result = response["Body"].read().decode("utf-8")
        parsed = json.loads(result)
        return parsed["embeddings"] if isinstance(parsed, dict) and "embeddings" in parsed else parsed


async def main():
    print("[*] Connecting to RabbitMQ...")
    connection = await aio_pika.connect_robust(AMQP_URL)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=MAX_CONCURRENT_BATCHES * BATCH_SIZE)

    await channel.declare_queue(INPUT_QUEUE, durable=True)
    await channel.declare_queue(OUTPUT_QUEUE, durable=True)

    queue = await channel.get_queue(INPUT_QUEUE)

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_BATCHES)
    embedder = BatchEmbedder(SAGEMAKER_ENDPOINT, AWS_REGION, channel, semaphore)

    await queue.consume(embedder.handle_message)
    print(f"[*] Waiting for messages on queue '{INPUT_QUEUE}'...")

    try:
        await asyncio.Future()
    finally:
        await connection.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted. Exiting.")
