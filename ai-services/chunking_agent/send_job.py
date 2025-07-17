import pika
import json
import os

# 👇 Dùng IP của RabbitMQ server
RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://admin:admin@52.65.216.159:5672/")
QUEUE_NAME = "chunking-queue"

params = pika.URLParameters(RABBITMQ_URL)
connection = pika.BlockingConnection(params)
channel = connection.channel()

channel.queue_declare(queue=QUEUE_NAME, durable=True)

# 📝 Sample job payload
job = {
    "s3Bucket": "your-s3-bucket",
    "s3Key": "path/to/your.md",
    "documentId": "doc123",
    "fileType": "md"
}

channel.basic_publish(
    exchange='',
    routing_key=QUEUE_NAME,
    body=json.dumps(job),
    properties=pika.BasicProperties(
        delivery_mode=2  # make message persistent
    )
)

print("[✅] Job sent to queue.")
connection.close()
