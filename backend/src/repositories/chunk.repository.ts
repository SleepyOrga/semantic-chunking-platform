// src/chunk/repositories/chunk.repository.ts
import { Injectable, Inject } from '@nestjs/common';
import { Knex } from 'knex';
import { AddChunkDto, UpdateChunkDto } from '../dto/chunk.dto';

@Injectable()
export class ChunkRepository {
  constructor(@Inject('KNEX_CONNECTION') private readonly knex: Knex) {}

  async findOne(id: string): Promise<any> {
    return this.knex('chunks')
      .where('id', id)
      .first();
  }

  async findByDocumentId(documentId: string): Promise<any[]> {
    return this.knex('chunks')
      .where('document_id', documentId)
      .orderBy('chunk_index', 'asc');
  }

  async create(data: AddChunkDto): Promise<string> {
    console.log("Creating chunk with data:", data);
    const [result] = await this.knex('chunks')
      .insert({
        document_id: data.document_id,
        chunk_index: data.chunk_index,
        content: data.content,
        embedding: data.embedding ? this.knex.raw(`ARRAY[${data.embedding.join(',')}]::vector`) : null,
        tags: data.tags || null,
        created_at: new Date()
      })
      .returning('id');
    
    return result.id;
  }

  async update(data: UpdateChunkDto): Promise<void> {
    const updateData: any = {};
    
    if (data.content !== undefined) {
      updateData.content = data.content;
    }
    
    if (data.embedding !== undefined) {
        updateData.embedding = this.knex.raw(`ARRAY[${data.embedding.join(',')}]::vector`);
    }
    
    if (data.tags !== undefined) {
      updateData.tags = data.tags;
    }
    
    await this.knex('chunks')
      .where('id', data.id)
      .update(updateData);
  }

  async delete(id: string): Promise<void> {
    await this.knex('chunks')
      .where('id', id)
      .delete();
  }

  async deleteByDocumentId(documentId: string): Promise<number> {
    return this.knex('chunks')
      .where('document_id', documentId)
      .delete();
  }

  async searchSimilar(embedding: number[], limit = 5, threshold = 0.7): Promise<any[]> {
    const embeddingStr = embedding;
    
    // Use pgvector's cosine similarity for search
    const results = await this.knex.raw(`
      SELECT 
        c.id,
        c.document_id,
        c.chunk_index,
        c.content,
        c.tags,
        1 - (c.embedding <=> ?) as similarity
      FROM 
        chunks c
      WHERE 
        1 - (c.embedding <=> ?) >= ?
      ORDER BY 
        similarity DESC
      LIMIT ?
    `, [embeddingStr, embeddingStr, threshold, limit]);
    
    return results.rows;
  }

  // New methods for tag operations

  // Update tags for a chunk
  async updateTags(id: string, tags: string[]): Promise<void> {
    await this.knex('chunks')
      .where('id', id)
      .update({ tags });
  }

  // Get tags for a chunk
  async getChunkTags(id: string): Promise<string[]> {
    const result = await this.knex('chunks')
      .where('id', id)
      .select('tags')
      .first();
    
    return result?.tags || [];
  }

  // Find chunks by tags (ANY match)
  async findByTags(tags: string[], limit = 10): Promise<any[]> {
    return this.knex('chunks')
      .whereRaw('tags && ?::text[]', [tags])
      .orderBy('created_at', 'desc')
      .limit(limit);
  }

  // Find chunks by tags (ALL match)
  async findByAllTags(tags: string[], limit = 10): Promise<any[]> {
    return this.knex('chunks')
      .whereRaw('tags @> ?::text[]', [tags])
      .orderBy('created_at', 'desc')
      .limit(limit);
  }
}