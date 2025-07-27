import { Module } from '@nestjs/common';
import { RabbitMQService } from './rabbitmq.service';
//import { ParserConsumerService } from './parser-consumer.service'; // Removed old parser consumer
//import { ChunkEmbeddingConsumerService } from './chunk-embedding-consumer.service';
import { ChunkModule } from 'src/chunk/chunk.module';

@Module({
  imports: [ChunkModule],
  providers: [
    RabbitMQService,
    // ParserConsumerService, // Removed old parser consumer since we now use Parser Gateway
  ],
  exports: [RabbitMQService], // Export RabbitMQService so other modules can use it
})
export class QueueModule {}
