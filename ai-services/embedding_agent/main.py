import asyncio
import json
import os
import sys
import boto3
import aio_pika
import aiohttp
from dotenv import load_dotenv
from typing import List

load_dotenv()

# RabbitMQ config
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "52.65.216.159")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "admin")
AMQP_URL = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"

# SageMaker config
SAGEMAKER_ENDPOINT = os.getenv("SAGEMAKER_EMBEDDING_ENDPOINT", "embedding-endpoint")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Backend API config
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:4000")

# Queue config
INPUT_QUEUE = "embedding-input-queue"

# Batch and concurrency config
BATCH_SIZE = 5
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
        self.http_session = None

    async def start_session(self):
        self.http_session = aiohttp.ClientSession()

    async def close_session(self):
        if self.http_session:
            await self.http_session.close()

    async def handle_message(self, message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                data = json.loads(message.body.decode())
                text = data.get("content")
                chunk_id = data.get("id")
                message_type = data.get("type")

                if not text or not chunk_id or not message_type:
                    print("[!] Skipping message: missing 'content', 'id', or 'type' field")
                    return

                if message_type not in ["chunk", "proposition"]:
                    print(f"[!] Skipping message: unknown type '{message_type}'")
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
                raise  # Re-raise to trigger message nack

    async def process_batch(self):
        if not self.pending_messages or not self.pending_texts:
            await self._cancel_timer()
            self.pending_messages.clear()
            self.pending_texts.clear()
            return

        await self._cancel_timer()
        batch_messages = self.pending_messages.copy()
        batch_texts = self.pending_texts.copy()
        batch_size = len(batch_texts)
        
        # Clear pending lists immediately to avoid race conditions
        self.pending_messages.clear()
        self.pending_texts.clear()
        
        print(f"[>] Processing batch of size {batch_size}")

        async with self.semaphore:
            try:
                embeddings = await self._call_sagemaker(batch_texts)

                if not isinstance(embeddings, list) or len(embeddings) != batch_size:
                    raise ValueError("SageMaker returned invalid or mismatched number of embeddings")

                for (message, original_data), embedding in zip(batch_messages, embeddings):
                    chunk_id = original_data["id"]
                    message_type = original_data["type"]
                    
                    if message_type == "chunk":
                        url = f"{BACKEND_URL}/chunks"
                        payload = {
                            "id": chunk_id,
                            "embedding": embedding
                        }
                    elif message_type == "proposition":
                        url = f"{BACKEND_URL}/chunk-components/{chunk_id}"
                        payload = {
                            "embedding": embedding
                        }

                    async with self.http_session.put(
                        url,
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status == 200:
                            print(f"[✓] Sent embedding for {message_type} {chunk_id}")
                        else:
                            print(f"[!] Failed to send embedding for {message_type} {chunk_id}: {response.status}")
                            # Note: We can't nack individual messages here since they're processed in batches
                            # The message.process() context manager will handle this based on exceptions

            except Exception as e:
                print(f"[!] Failed to process batch: {e}", file=sys.stderr)
                # Don't re-raise here as messages are already processed by their context managers

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

    queue = await channel.get_queue(INPUT_QUEUE)

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_BATCHES)
    embedder = BatchEmbedder(SAGEMAKER_ENDPOINT, AWS_REGION, channel, semaphore)
    await embedder.start_session()

    await queue.consume(embedder.handle_message)
    print(f"[*] Waiting for messages on queue '{INPUT_QUEUE}'...")

    try:
        await asyncio.Future()
    finally:
        await embedder.close_session()
        await connection.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted. Exiting.")
