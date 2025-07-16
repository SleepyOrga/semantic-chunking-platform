// src/tags/tags.service.ts
import { Injectable, NotFoundException, ConflictException } from '@nestjs/common';
import { TagRepository } from '../repositories/tag.repository';
import { CreateTagDto, UpdateTagDto } from '../dto/tag.dto';

@Injectable()
export class TagsService {
  constructor(private readonly tagRepository: TagRepository) {}

  async findAll(search?: string) {
    const tags = await this.tagRepository.findAll(search);
    return { tags };
  }

  async findOne(id: number) {
    const tag = await this.tagRepository.findOne(id);
    if (!tag) {
      throw new NotFoundException(`Tag with ID ${id} not found`);
    }
    return { tag };
  }

  async create(createTagDto: CreateTagDto) {
    try {
      // Check if tag already exists
      const existingTag = await this.tagRepository.findByName(createTagDto.name);
      if (existingTag) {
        throw new ConflictException(`Tag "${createTagDto.name}" already exists`);
      }

      const tagId = await this.tagRepository.create(createTagDto);
      const tag = await this.tagRepository.findOne(tagId);
      return { tag, message: 'Tag created successfully' };
    } catch (error) {
      if (error instanceof ConflictException) {
        throw error;
      }
      throw new Error(`Failed to create tag: ${error.message}`);
    }
  }

  async update(id: number, updateTagDto: UpdateTagDto) {
    const tag = await this.tagRepository.findOne(id);
    if (!tag) {
      throw new NotFoundException(`Tag with ID ${id} not found`);
    }

    // Check if updated name already exists (but not for this tag)
    if (updateTagDto.name && updateTagDto.name !== tag.name) {
      const existingTag = await this.tagRepository.findByName(updateTagDto.name);
      if (existingTag && existingTag.id !== id) {
        throw new ConflictException(`Tag "${updateTagDto.name}" already exists`);
      }
    }

    await this.tagRepository.update(id, updateTagDto);
    const updatedTag = await this.tagRepository.findOne(id);
    return { tag: updatedTag, message: 'Tag updated successfully' };
  }

  async remove(id: number) {
    const tag = await this.tagRepository.findOne(id);
    if (!tag) {
      throw new NotFoundException(`Tag with ID ${id} not found`);
    }

    await this.tagRepository.remove(id);
    return { message: 'Tag deleted successfully' };
  }
}