import { Module } from '@nestjs/common';
import { ChunkComponentController } from './chunk-component.controller';
import { ChunkComponentService } from './chunk-component.service';
import { ChunkComponentRepository } from '../repositories/chunk-component.repository';

@Module({
  controllers: [ChunkComponentController],
  providers: [ChunkComponentService, ChunkComponentRepository],
  exports: [ChunkComponentService]
})
export class ChunkComponentModule {}