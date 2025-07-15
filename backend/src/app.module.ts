import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { AppController } from './upload/upload.controller';
import { RabbitMQService } from './queue/rabbitmq.service';
import { DocumentModule } from './document/document.module';
import { ChunkModule } from './chunk/chunk.module';
import { KnexModule } from './database/knex.module';
import { AuthModule } from './auth/auth.module';
import { QueueModule } from './queue/queue.module';
import { UploadModule } from './upload/upload.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
    }),
    DocumentModule,
    ChunkModule,
    KnexModule,
    AuthModule,
    QueueModule,
    UploadModule
  ],
  controllers: [AppController],
  providers: [RabbitMQService],
})
export class AppModule {}
