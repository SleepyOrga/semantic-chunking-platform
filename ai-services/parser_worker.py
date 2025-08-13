#!/usr/bin/env python3
"""
Independent parser worker that processes files from a RabbitMQ queue.
Each worker is responsible for a specific file type (pdf, docx, xlsx).
"""

import os
import sys
import json
import logging
import pika
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ParserWorker:
    def __init__(self, parser_type: str, rabbitmq_url: str):
        """Initialize the parser worker.
        
        Args:
            parser_type: Type of parser (pdf, docx, xlsx)
            rabbitmq_url: URL to connect to RabbitMQ
        """
        self.parser_type = parser_type
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None
        
        # Map parser types to their respective modules and functions
        self.parser_config = {
            'pdf': {
                'module': 'ocr_parser.main',
                'function': 'process_document'
            },
            'docx': {
                'module': 'xlsx_docx_parser.parser_docx',
                'function': 'extract_docx_to_markdown'
            },
            'xlsx': {
                'module': 'xlsx_docx_parser.parser_xlsx',
                'function': 'extract_xlsx_to_markdown'
            }
        }

    def connect(self):
        """Establish connection to RabbitMQ."""
        try:
            self.connection = pika.BlockingConnection(
                pika.URLParameters(self.rabbitmq_url)
            )
            self.channel = self.connection.channel()
            
            # Declare queues
            self.channel.queue_declare(queue=f'{self.parser_type}-parser-queue', durable=True)
            self.channel.queue_declare(queue='chunking-queue', durable=True)
            
            logger.info(f"✅ Connected to RabbitMQ and listening on {self.parser_type}-parser-queue")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def process_message(self, ch, method, properties, body):
        """Process incoming message from the queue."""
        try:
            payload = json.loads(body)
            logger.info(f"📩 Received message: {payload}")
            
            # Extract necessary information from payload
            s3_key = payload.get('s3Key')
            filename = payload.get('filename', 'unknown')
            document_id = payload.get('documentId')
            s3_bucket = os.getenv('S3_BUCKET_NAME', 'semantic-chunking-bucket')
            
            # Generate output path
            output_s3_prefix = f"parsed/{document_id}/"
            
            # Get the appropriate parser function
            parser_module = __import__(
                self.parser_config[self.parser_type]['module'],
                fromlist=[self.parser_config[self.parser_type]['function']]
            )
            parser_func = getattr(
                parser_module, 
                self.parser_config[self.parser_type]['function']
            )
            
            # Call the appropriate parser function
            if self.parser_type == 'pdf':
                result = parser_func(
                    input_file=s3_key,
                    output_dir=output_s3_prefix,
                    s3_bucket=s3_bucket,
                    s3_prefix=output_s3_prefix
                )
            else:
                result = parser_func(
                    input_path=s3_key,
                    output_dir=output_s3_prefix,
                    s3_bucket=s3_bucket,
                    s3_prefix=output_s3_prefix
                )
            
            # Send result to chunking queue
            chunking_payload = {
                's3Bucket': s3_bucket,
                's3Key': result,
                'documentId': document_id,
                'fileType': self.parser_type
            }
            
            self.channel.basic_publish(
                exchange='',
                routing_key='chunking-queue',
                body=json.dumps(chunking_payload),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                )
            )
            
            logger.info(f"✅ Successfully processed {filename}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}", exc_info=True)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def start_consuming(self):
        """Start consuming messages from the queue."""
        try:
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue=f'{self.parser_type}-parser-queue',
                on_message_callback=self.process_message,
                auto_ack=False
            )
            
            logger.info(f"🔄 Waiting for messages in {self.parser_type}-parser-queue...")
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("\n👋 Shutting down worker...")
            if self.connection:
                self.connection.close()
            sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description='Run a parser worker for a specific file type')
    parser.add_argument('--type', type=str, required=True, choices=['pdf', 'docx', 'xlsx'],
                       help='Type of parser to run (pdf, docx, xlsx)')
    parser.add_argument('--rabbitmq', type=str, 
                       default='amqp://admin:admin@52.65.216.159:5672',
                       help='RabbitMQ connection URL')
    
    args = parser.parse_args()
    
    # Create and start worker
    worker = ParserWorker(args.type, args.rabbitmq)
    worker.connect()
    worker.start_consuming()

if __name__ == "__main__":
    main()
