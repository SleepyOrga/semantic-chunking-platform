import pika
import os

# 👇 Trỏ về RabbitMQ server IP thật
RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://admin:admin@52.65.216.159:5672/")
QUEUE_NAME = "chunking-queue"

params = pika.URLParameters(RABBITMQ_URL)
connection = pika.BlockingConnection(params)
channel = connection.channel()

method_frame, header_frame, body = channel.basic_get(queue=QUEUE_NAME, auto_ack=True)

if method_frame:
    print("[✅] Found a message in queue:")
    print(body)
else:
    print("[❌] Queue is empty.")
