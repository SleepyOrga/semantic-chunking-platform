import { Module } from '@nestjs/common';
import { RabbitMQService } from './rabbitmq.service';
import { ParserConsumerService } from './parser-consumer.service';
import { UploadModule } from 'src/upload/upload.module';

@Module({
  imports: [UploadModule],
  providers: [RabbitMQService, ParserConsumerService],
})
export class QueueModule {}
