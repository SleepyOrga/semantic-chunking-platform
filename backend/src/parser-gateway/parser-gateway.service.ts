import { Injectable, OnModuleInit } from '@nestjs/common';
import { RabbitMQService } from '../queue/rabbitmq.service';

interface FileProcessMessage {
  username: string;
  filename: string;
  s3Key: string;
  uploadedAt: string;
  fileType: 'docx' | 'pdf' | 'xlsx' | 'image' | 'unknown';
  documentId: string;
}

@Injectable()
export class ParserGatewayService implements OnModuleInit {
  constructor(private readonly rabbitMQService: RabbitMQService) {}

  async onModuleInit() {
    // Ensure parser queues exist
    await this.rabbitMQService.awaitConnection();
    await this.setupParserQueues();
    
    // Start consuming from file-process-queue
    await this.startProcessing();
  }

  private async setupParserQueues() {
    const queues = ['docx-parser-queue', 'pdf-parser-queue', 'xlsx-parser-queue'];
    
    for (const queueName of queues) {
      await this.rabbitMQService.assertQueue(queueName, { durable: true });
      console.log(`✅ Parser queue '${queueName}' is ready`);
    }
  }

  private async startProcessing() {
    console.log('🚀 Parser Gateway starting to consume from file-process-queue...');
    
    await this.rabbitMQService.consume('file-process-queue', async (msg) => {
      if (msg?.content) {
        try {
          const message: FileProcessMessage = JSON.parse(msg.content.toString());
          console.log(`📄 Parser Gateway received: ${message.filename} (${message.fileType})`);
          
          await this.routeToParserQueue(message);
          
          // Acknowledge the message
          this.rabbitMQService.ackMessage(msg);
          console.log(`✅ Message routed successfully: ${message.filename}`);
          
        } catch (error) {
          console.error('❌ Error processing message in Parser Gateway:', error);
          // Reject and requeue the message for retry
          this.rabbitMQService.nackMessage(msg, false, true);
        }
      }
    });
  }

  private async routeToParserQueue(message: FileProcessMessage) {
    const { fileType } = message;
    let targetQueue: string;

    switch (fileType) {
      case 'docx':
        targetQueue = 'docx-parser-queue';
        break;
      case 'pdf':
        targetQueue = 'pdf-parser-queue';
        break;
      case 'xlsx':
        targetQueue = 'xlsx-parser-queue';
        break;
      case 'image':
        // Images can be processed by PDF parser (OCR)
        targetQueue = 'pdf-parser-queue';
        break;
      default:
        throw new Error(`Unsupported file type: ${fileType}`);
    }

    console.log(`🎯 Routing ${message.filename} to ${targetQueue}`);
    
    await this.rabbitMQService.sendToQueue(message, targetQueue);
  }
}
