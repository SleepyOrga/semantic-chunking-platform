// src/tags/tags.service.ts
import { Injectable, Inject, ConflictException, NotFoundException } from '@nestjs/common';
import { Knex } from 'knex';
import { CreateTagDto, UpdateTagDto } from '../dto/tag.dto';

@Injectable()
export class TagsService {
  constructor(@Inject('KNEX_CONNECTION') private readonly knex: Knex) {}

  async findAll(search?: string): Promise<any[]> {
    let query = this.knex('tags').orderBy('name', 'asc');
    
    if (search) {
      query = query.whereILike('name', `%${search}%`);
    }
    
    return query;
  }

  async findOne(id: number): Promise<any> {
    const tag = await this.knex('tags').where('id', id).first();
    
    if (!tag) {
      throw new NotFoundException(`Tag with ID ${id} not found`);
    }
    
    return tag;
  }

  async findByName(name: string): Promise<any> {
    return this.knex('tags').where('name', name).first();
  }

  async create(createTagDto: CreateTagDto): Promise<any> {
    try {
      // Check if tag already exists
      const existingTag = await this.findByName(createTagDto.name);
      if (existingTag) {
        throw new ConflictException(`Tag with name '${createTagDto.name}' already exists`);
      }

      const [result] = await this.knex('tags')
        .insert({
          name: createTagDto.name,
          created_at: new Date()
        })
        .returning('*');
      
      return result;
    } catch (error) {
      // Handle database unique constraint error
      if (error.code === '23505' || error.constraint?.includes('tags_name_unique')) {
        throw new ConflictException(`Tag with name '${createTagDto.name}' already exists`);
      }
      throw error;
    }
  }

  async update(id: number, updateTagDto: UpdateTagDto): Promise<any> {
    try {
      // Check if tag exists
      await this.findOne(id);
      
      // Check if new name conflicts with existing tag
      if (updateTagDto.name) {
        const existingTag = await this.findByName(updateTagDto.name);
        if (existingTag && existingTag.id !== id) {
          throw new ConflictException(`Tag with name '${updateTagDto.name}' already exists`);
        }
      }

      const [result] = await this.knex('tags')
        .where('id', id)
        .update(updateTagDto)
        .returning('*');
      
      return result;
    } catch (error) {
      if (error.code === '23505' || error.constraint?.includes('tags_name_unique')) {
        throw new ConflictException(`Tag with name '${updateTagDto.name}' already exists`);
      }
      throw error;
    }
  }

  async remove(id: number): Promise<void> {
    const tag = await this.findOne(id);
    
    await this.knex('tags').where('id', id).delete();
  }

  async createIfNotExists(name: string): Promise<any> {
    const existingTag = await this.findByName(name);
    if (existingTag) {
      return existingTag;
    }
    
    return this.create({ name });
  }
}