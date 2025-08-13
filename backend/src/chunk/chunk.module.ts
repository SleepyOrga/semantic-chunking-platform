import { Module } from '@nestjs/common';
import { ChunkService } from './chunk.service';
import { ChunkRepository } from '../repositories/chunk.repository';
import { DocumentRepository } from '../repositories/document.repository';
import { ChunkController } from './chunk.controller';

@Module({
  providers: [
    ChunkService,
    ChunkRepository,
    DocumentRepository, // We need this because ChunkService validates document existence
  ],
  exports: [
    ChunkService,
  ],
  controllers: [ChunkController],
})
export class ChunkModule {}