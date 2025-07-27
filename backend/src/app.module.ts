import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { DocumentModule } from './document/document.module';
import { ChunkModule } from './chunk/chunk.module';
import { KnexModule } from './database/knex.module';
import { AuthModule } from './auth/auth.module';
import { QueueModule } from './queue/queue.module';
import { UploadModule } from './upload/upload.module';
import { TagsModule } from './tags/tag.module';
import { ChunkComponentModule } from './chunk-component/chunk-component.module';
import { ParserGatewayModule } from './parser-gateway/parser-gateway.module';

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
    UploadModule,
    TagsModule,
    ChunkComponentModule,
    ParserGatewayModule,
  ],
  controllers: [], // Moved AppController to UploadModule where it belongs
  providers: [],
})
export class AppModule {}
