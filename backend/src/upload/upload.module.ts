import { Module } from '@nestjs/common';
import { S3Service } from './s3.service';
import { AppController } from './upload.controller';
import { QueueModule } from '../queue/queue.module';
import { DocumentModule } from '../document/document.module';

@Module({
  imports: [QueueModule, DocumentModule],
  controllers: [AppController],
  providers: [S3Service],
  exports: [S3Service], 
})
export class UploadModule {}
