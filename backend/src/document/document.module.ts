import { Module, forwardRef } from '@nestjs/common';
import { DocumentService } from './document.service';
import { DocumentRepository } from '../repositories/document.repository';
import { DocumentController } from './document.controller';
import { UploadModule } from '../upload/upload.module';
import { ChunkModule } from '../chunk/chunk.module';

@Module({
  imports: [forwardRef(() => UploadModule), ChunkModule],
  providers: [
    DocumentService,
    DocumentRepository,
  ],
  exports: [
    DocumentService,
  ],
  controllers: [
    DocumentController,
  ],
})
export class DocumentModule {}