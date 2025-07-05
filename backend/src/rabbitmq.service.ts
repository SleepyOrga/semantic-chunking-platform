import { Injectable, OnModuleInit } from '@nestjs/common';
import * as amqp from 'amqplib';

@Injectable()
export class RabbitMQService implements OnModuleInit {
  private channel: amqp.Channel;

  async onModuleInit() {
    const conn = await amqp.connect('amqp://admin:admin@54.92.209.245:5672');
    this.channel = await conn.createChannel();
    await this.channel.assertQueue('file-process-queue', { durable: true });
  }

  async sendToQueue(data: any) {
    if (!this.channel) throw new Error('Channel not initialized');
    this.channel.sendToQueue(
      'file-process-queue',
      Buffer.from(JSON.stringify(data)),
      { persistent: true }
    );
  }
}
