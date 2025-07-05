import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { AppController } from './app.controller';
import { S3Service } from './s3.service';
import { RabbitMQService } from './rabbitmq.service';

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
