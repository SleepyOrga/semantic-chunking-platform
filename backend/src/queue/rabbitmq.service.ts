import { Injectable, OnModuleInit, Logger } from '@nestjs/common';
import * as amqp from 'amqplib';

@Injectable()
export class RabbitMQService implements OnModuleInit {
  private channel: amqp.Channel;
  private connection: amqp.Connection;
  private readonly logger = new Logger(RabbitMQService.name);
  private readonly RABBITMQ_URL = process.env.RABBITMQ_URL || 'amqp://admin:admin@52.65.216.159:5672';
  private readonly MAX_RETRIES = 3;

  async onModuleInit() {
    await this.initialize();
  }

  private async initialize() {
    try {
      // Connect to RabbitMQ
      this.connection = await amqp.connect(this.RABBITMQ_URL);
      this.connection.on('error', (err) => {
        this.logger.error('RabbitMQ connection error:', err);
        // Attempt to reconnect after a delay
        setTimeout(() => this.initialize(), 5000);
      });

      // Create a new channel
      this.channel = await this.connection.createChannel();
      
      // Set prefetch to 1 to process one message at a time
      await this.channel.prefetch(1);
      
      // Define all queues we need
      const queues = [
        'file-process-queue',
        'pdf-parser-queue',
        'docx-parser-queue',
        'xlsx-parser-queue',
        'chunking-queue'
      ];
      
      // Create queues if they don't exist
      for (const queue of queues) {
        try {
          // Try to declare the queue with DLX first
          await this.channel.assertQueue(queue, { 
            durable: true,
            deadLetterExchange: 'dlx',
            deadLetterRoutingKey: `${queue}-dlq`
          });
          this.logger.log(`✅ Queue declared: ${queue}`);
        } catch (error) {
          // If DLX setup fails, fall back to basic queue
          if (error.message.includes('PRECONDITION_FAILED')) {
            this.logger.warn(`DLX not available for ${queue}, falling back to basic queue`);
            await this.channel.assertQueue(queue, { durable: true });
          } else {
            throw error;
          }
        }
      }
      
      // Set up DLX and DLQs if possible
      try {
        await this.channel.assertExchange('dlx', 'direct', { durable: true });
        
        const dlqs = queues.map(q => `${q}-dlq`);
        for (const dlq of dlqs) {
          await this.channel.assertQueue(dlq, { durable: true });
          await this.channel.bindQueue(dlq, 'dlx', dlq);
        }
        this.logger.log('✅ DLX and DLQs set up successfully');
      } catch (error) {
        this.logger.warn('Failed to set up DLX/DLQs, continuing without them:', error.message);
      }
      
      this.logger.log('✅ RabbitMQ initialized with all queues and DLQs');
      
    } catch (error) {
      this.logger.error('Failed to initialize RabbitMQ:', error);
      throw error;
    }
  }

  async awaitConnection(): Promise<void> {
    let attempts = 0;
    while (!this.channel && attempts < this.MAX_RETRIES) {
      attempts++;
      await new Promise((res) => setTimeout(res, 1000));
    }
    if (!this.channel) {
      throw new Error('Failed to establish RabbitMQ connection after retries');
    }
  }

  async consume(queue: string, onMessage: (msg: amqp.ConsumeMessage | null) => void) {
    if (!this.channel) {
      throw new Error('Channel not initialized');
    }
    
    try {
      const { consumerTag } = await this.channel.consume(queue, (msg) => {
        if (msg) {
          try {
            onMessage(msg);
          } catch (error) {
            this.logger.error(`Error processing message from ${queue}:`, error);
            this.channel.nack(msg, false, false); // Reject message without requeue
          }
        }
      }, { 
        noAck: false,
        prefetch: 1 // Process one message at a time
      });
      
      this.logger.log(`✅ Started consuming from ${queue} with consumer tag: ${consumerTag}`);
      return consumerTag;
    } catch (error) {
      this.logger.error(`Failed to start consuming from ${queue}:`, error);
      throw error;
    }
  }

  async sendToQueue(data: any, queueName: string = 'file-process-queue', options: amqp.Options.Publish = {}) {
    if (!this.channel) {
      throw new Error('Channel not initialized');
    }
    
    try {
      const message = Buffer.from(JSON.stringify(data));
      const defaultOptions: amqp.Options.Publish = {
        persistent: true,
        contentType: 'application/json',
        ...options,
      };
      
      const success = this.channel.sendToQueue(queueName, message, defaultOptions);
      if (!success) {
        throw new Error(`Failed to publish message to ${queueName} - queue is full`);
      }
      
      return success;
    } catch (error) {
      this.logger.error(`Failed to send message to ${queueName}:`, error);
      throw error;
    }
  }
  
  async close() {
    try {
      if (this.channel) {
        await this.channel.close();
        this.channel = null;
      }
      if (this.connection) {
        await this.connection.close();
        this.connection = null;
      }
      this.logger.log('RabbitMQ connection closed');
    } catch (error) {
      this.logger.error('Error closing RabbitMQ connection:', error);
      throw error;
    }
  }
}
