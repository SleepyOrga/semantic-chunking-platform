import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { AppController } from './upload/upload.controller';
import { S3Service } from './upload/s3.service';
import { RabbitMQService } from './queue/rabbitmq.service';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
    }),
  ],
  controllers: [AppController],
  providers: [S3Service, RabbitMQService],
})
export class AppModule {}
