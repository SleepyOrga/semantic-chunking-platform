import { Module } from '@nestjs/common';
import { TagsController } from './tag.controller';
import { TagsService } from './tag.service';
import { TagRepository } from '../repositories/tag.repository';

@Module({
  controllers: [TagsController],
  providers: [TagsService, TagRepository],
  exports: [TagsService]
})
export class TagsModule {}