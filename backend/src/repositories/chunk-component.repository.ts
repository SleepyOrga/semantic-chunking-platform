import { Injectable, Inject } from '@nestjs/common';
import { Knex } from 'knex';
import { 
  CreateChunkComponentDto, 
  UpdateChunkComponentDto 
} from '../dto/chunk-component.dto';

@Injectable()
export class ChunkComponentRepository {
  constructor(@Inject('KNEX_CONNECTION') private readonly knex: Knex) {}

  async findByChunkId(chunkId: string): Promise<any[]> {
    return this.knex('chunk_components')
      .where('chunk_id', chunkId)
      .orderBy('component_index', 'asc');
  }

  async findOne(id: string): Promise<any> {
    return this.knex('chunk_components')
      .where('id', id)
      .first();
  }

  async create(createDto: CreateChunkComponentDto): Promise<string> {
    const [result] = await this.knex('chunk_components')
      .insert({
        chunk_id: createDto.chunk_id,
        component_index: createDto.component_index,
        content: createDto.content,
        embedding: createDto.embedding ? this.knex.raw(`ARRAY[${createDto.embedding.join(',')}]::vector`) : null,
        created_at: new Date()
      })
      .returning('id');
    
    return result.id;
  }

  async createBulk(createDtos: CreateChunkComponentDto[]): Promise<string[]> {
    // Format the data for bulk insert
    const records = createDtos.map(dto => ({
      chunk_id: dto.chunk_id,
      component_index: dto.component_index,
      content: dto.content,
      embedding: dto.embedding ? this.knex.raw(`ARRAY[${dto.embedding.join(',')}]::vector`) : null,
      created_at: new Date()
    }));
    
    // Perform bulk insert and return IDs
    const results = await this.knex('chunk_components')
      .insert(records)
      .returning('id');
    
    return results.map(r => r.id);
  }

  async update(id: string, updateDto: UpdateChunkComponentDto): Promise<void> {
    const updateData: any = {};
    
    if (updateDto.content !== undefined) {
      updateData.content = updateDto.content;
    }
    
    if (updateDto.embedding !== undefined) {
      updateData.embedding = updateDto.embedding ? this.knex.raw(`ARRAY[${updateDto.embedding.join(',')}]::vector`) : null;
    }
    
    if (updateDto.component_index !== undefined) {
      updateData.component_index = updateDto.component_index;
    }
    
    await this.knex('chunk_components')
      .where('id', id)
      .update(updateData);
  }

  async remove(id: string): Promise<void> {
    await this.knex('chunk_components')
      .where('id', id)
      .delete();
  }

  async removeByChunkId(chunkId: string): Promise<number> {
    const result = await this.knex('chunk_components')
      .where('chunk_id', chunkId)
      .delete();
    
    return result;
  }

  async searchSimilar(embedding: number[], limit = 5, threshold = 0.7): Promise<any[]> {
    // Use pgvector's cosine similarity to find similar components
    const results = await this.knex.raw(`
      SELECT 
        cc.id,
        cc.chunk_id,
        cc.component_index,
        cc.content,
        c.document_id,
        1 - (cc.embedding <=> ARRAY[${embedding.join(',')}]::vector) as similarity
      FROM 
        chunk_components cc
      JOIN
        chunks c ON cc.chunk_id = c.id
      WHERE 
        1 - (cc.embedding <=> ARRAY[${embedding.join(',')}]::vector) >= ?
      ORDER BY 
        similarity DESC
      LIMIT ?
    `, [threshold, limit]);
    
    return results.rows;
  }
}