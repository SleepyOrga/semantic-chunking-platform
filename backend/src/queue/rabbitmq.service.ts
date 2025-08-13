import { Injectable, OnModuleInit } from '@nestjs/common';
import * as amqp from 'amqplib';

@Injectable()
export class RabbitMQService implements OnModuleInit {
  private channel: amqp.Channel;

  async onModuleInit() {
    const conn = await amqp.connect('amqp://admin:admin@52.65.216.159:5672');
    this.channel = await conn.createChannel();
    await this.channel.assertQueue('file-process-queue', { durable: true });
    await this.channel.assertQueue('chunking-queue', { durable: true });
  }

  async awaitConnection(): Promise<void> {
    while (!this.channel) {
      await new Promise((res) => setTimeout(res, 100));
    }
  }

  async assertQueue(queueName: string, options: any = { durable: true }) {
    if (!this.channel) throw new Error('Channel not initialized');
    return await this.channel.assertQueue(queueName, options);
  }

  async consume(queue: string, onMessage: (msg: any) => void) {
    if (!this.channel) throw new Error('Channel not initialized');
    this.channel.consume(queue, onMessage, { noAck: false });
  }

  ackMessage(msg: any) {
    if (!this.channel) throw new Error('Channel not initialized');
    this.channel.ack(msg);
  }

  nackMessage(msg: any, allUpTo: boolean = false, requeue: boolean = true) {
    if (!this.channel) throw new Error('Channel not initialized');
    this.channel.nack(msg, allUpTo, requeue);
  }

  async sendToQueue(data: any, queueName: string = 'file-process-queue') {
    if (!this.channel) throw new Error('Channel not initialized');
    this.channel.sendToQueue(
      queueName,
      Buffer.from(JSON.stringify(data)),
      { persistent: true },
    );
  }
}
