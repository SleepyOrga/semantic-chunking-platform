import { Module } from '@nestjs/common';
import { DocumentService } from './document.service';
import { DocumentRepository } from '../repositories/document.repository';
import { DocumentController } from './document.controller';

@Module({
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