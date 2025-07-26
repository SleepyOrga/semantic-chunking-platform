import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import { RabbitMQService } from './rabbitmq.service';

@Injectable()
export class ParserConsumerService implements OnModuleInit {
  private readonly logger = new Logger(ParserConsumerService.name);

  constructor(
    private readonly rabbitMQService: RabbitMQService,
  ) {}

  async onModuleInit() {
    this.logger.log('🔁 Waiting for RabbitMQ channel to be ready...');
    await this.rabbitMQService.awaitConnection();
    this.logger.log('✅ RabbitMQ channel ready. Starting file processor...');

    // Only consume from the file processing queue
    await this.rabbitMQService.consume(
      'file-process-queue',
      this.handleFileProcessMessage.bind(this),
    );
  }

  async handleFileProcessMessage(msg: any) {
    this.logger.log('📩 New message received from file-process-queue');
    
    try {
      const payload = JSON.parse(msg.content.toString());
      const { fileType, s3Key, filename, documentId } = payload;
  
      this.logger.debug(`📦 Raw Payload: ${JSON.stringify(payload)}`);
      
      // Route to the appropriate parser queue based on file type
      let targetQueue: string;
      
      switch (fileType) {
        case 'pdf':
          targetQueue = 'pdf-parser-queue';
          break;
        case 'docx':
          targetQueue = 'docx-parser-queue';
          break;
        case 'xlsx':
          targetQueue = 'xlsx-parser-queue';
          break;
        default:
          this.logger.warn(`❌ Unsupported file type: ${fileType}`);
          this.rabbitMQService['channel'].ack(msg);
          return;
      }
      
      // Forward the message to the appropriate parser queue
      await this.rabbitMQService.sendToQueue(payload, targetQueue);
      this.logger.log(`📤 Routed ${fileType} file to ${targetQueue}`);
      this.rabbitMQService['channel'].ack(msg);
      
    } catch (error) {
      this.logger.error('🔥 Error while processing file-process-queue message:', error);
      this.rabbitMQService['channel'].nack(msg, false, false);
    }
  }
  
  // Removed handleParserMessage since parsers now send to chunking queue directly
}
