import { Module } from '@nestjs/common';
import { RabbitMQService } from './rabbitmq.service';
import { ChunkModule } from 'src/chunk/chunk.module';

@Module({
  imports: [ChunkModule],
  providers: [
    RabbitMQService,
  ],
  exports: [RabbitMQService], 
})
export class QueueModule {}
