import { Injectable, Inject } from '@nestjs/common';
import { Knex } from 'knex';
import { CreateTagDto, UpdateTagDto } from '../dto/tag.dto';

@Injectable()
export class TagRepository {
  constructor(@Inject('KNEX_CONNECTION') private readonly knex: Knex) {}

  async findAll(search?: string): Promise<any[]> {
    const query = this.knex('tags')
      .select('*')
      .orderBy('name', 'asc');
    
    if (search) {
      query.where('name', 'ilike', `%${search}%`);
    }
    
    return query;
  }

  async findOne(id: number): Promise<any> {
    return this.knex('tags')
      .where('id', id)
      .first();
  }

  async findByName(name: string): Promise<any> {
    return this.knex('tags')
      .where('name', name)
      .first();
  }

  async create(createTagDto: CreateTagDto): Promise<number> {
    const [result] = await this.knex('tags')
      .insert({
        name: createTagDto.name,
        created_at: new Date()
      })
      .returning('id');
    
    return result.id;
  }

  async update(id: number, updateTagDto: UpdateTagDto): Promise<void> {
    await this.knex('tags')
      .where('id', id)
      .update({
        name: updateTagDto.name,
        // Don't update created_at
      });
  }

  async remove(id: number): Promise<void> {
    await this.knex('tags')
      .where('id', id)
      .delete();
  }
}