import { Module } from '@nestjs/common';
import { RabbitMQService } from './rabbitmq.service';
import { ParserConsumerService } from './parser-consumer.service';
import { UploadModule } from 'src/upload/upload.module';
//import { ChunkEmbeddingConsumerService } from './chunk-embedding-consumer.service';
import { ChunkModule } from 'src/chunk/chunk.module';

@Module({
  imports: [UploadModule, 
    ],
  providers: [
    RabbitMQService,
    ParserConsumerService,
    
  ],
})
export class QueueModule {}
