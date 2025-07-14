import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { AppController } from './app.controller';
import { S3Service } from './s3.service';
import { RabbitMQService } from './rabbitmq.service';
import { DocumentModule } from './document/document.module';
import { ChunkModule } from './chunk/chunk.module';
import { KnexModule } from './database/knex.module';
import { AuthModule } from './auth/auth.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
    }),
    DocumentModule,
    ChunkModule,
    KnexModule,
    AuthModule,
  ],
  controllers: [AppController],
  providers: [S3Service, RabbitMQService],
})
export class AppModule {}
