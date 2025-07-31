#!/usr/bin/env python3

import os
import pika
import json
from dotenv import load_dotenv

load_dotenv()

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://admin:admin@52.65.216.159:5672/")
CHUNKING_QUEUE = "chunking-queue"

def check_queue():
    try:
        # Connect to RabbitMQ
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        
        # Declare the queue (in case it doesn't exist)
        channel.queue_declare(queue=CHUNKING_QUEUE, durable=True)
        
        # Get queue info
        method = channel.queue_declare(queue=CHUNKING_QUEUE, durable=True, passive=True)
        message_count = method.method.message_count
        
        print(f"Queue '{CHUNKING_QUEUE}' has {message_count} messages")
        
        if message_count > 0:
            # Peek at the first message without consuming it
            method_frame, header_frame, body = channel.basic_get(queue=CHUNKING_QUEUE, auto_ack=False)
            
            if method_frame:
                try:
                    message = json.loads(body.decode())
                    print("Next message in queue:")
                    print(json.dumps(message, indent=2))
                except json.JSONDecodeError:
                    print("Message is not valid JSON:")
                    print(body.decode())
                
                # Put the message back
                channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=True)
            else:
                print("Could not retrieve message")
        else:
            print("Queue is empty")
        
        connection.close()
        
    except Exception as e:
        print(f"Error checking queue: {e}")

if __name__ == "__main__":
    check_queue()
