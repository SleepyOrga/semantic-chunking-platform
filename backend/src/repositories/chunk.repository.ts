import { Injectable, Inject } from '@nestjs/common';
import { Knex } from 'knex';
import {
  ChunkEntity,
  CreateChunkData,
  UpdateChunkData,
} from '../entities/chunk.entity';

@Injectable()
export class ChunkRepository {
  constructor(@Inject('KNEX_CONNECTION') private readonly knex: Knex) {}

  async create(data: CreateChunkData): Promise<string> {
    const [chunk] = await this.knex('chunks')
      .insert({
        document_id: data.document_id,
        chunk_index: data.chunk_index,
        content: data.content,
        embedding: JSON.stringify(data.embedding),
      })
      .returning('id');

    return chunk.id;
  }

  async findById(id: string): Promise<ChunkEntity | null> {
    const chunk = await this.knex('chunks').where('id', id).first();

    if (!chunk) return null;

    return {
      ...chunk,
      embedding: JSON.parse(chunk.embedding),
    };
  }

  async findByDocumentId(documentId: string): Promise<ChunkEntity[]> {
    const chunks = await this.knex('chunks')
      .where('document_id', documentId)
      .orderBy('chunk_index', 'asc');

    return chunks.map((chunk) => ({
      ...chunk,
      embedding: JSON.parse(chunk.embedding),
    }));
  }

  async update(id: string, data: UpdateChunkData): Promise<void> {
    const updateData = { ...data };

    if (updateData.embedding) {
      updateData.embedding = JSON.stringify(updateData.embedding) as any;
    }

    await this.knex('chunks').where('id', id).update(updateData);
  }

  async delete(id: string): Promise<void> {
    await this.knex('chunks').where('id', id).del();
  }

  async deleteByDocumentId(documentId: string): Promise<void> {
    await this.knex('chunks').where('document_id', documentId).del();
  }

  async exists(id: string): Promise<boolean> {
    try {
      const count = await this.knex('chunks')
        .where('id', id)
        .count('id as count')
        .first();

      return count ? parseInt(count.count as string) > 0 : false;
    } catch (error) {
      console.error(`Error checking if chunk exists: ${error.message}`);
      return false;
    }
  }

  async countByDocumentId(documentId: string): Promise<number> {
    try {
      const result = await this.knex('chunks')
        .where('document_id', documentId)
        .count('id as count')
        .first();

      return result ? parseInt(result.count as string) : 0;
    } catch (error) {
      console.error(`Error counting chunks by document ID: ${error.message}`);
      return 0;
    }
  }
  async searchSimilar(embedding: number[], limit = 10): Promise<ChunkEntity[]> {
    const chunks = await this.knex.raw(
      `
      SELECT c.*
      FROM chunks c
      JOIN documents d ON c.document_id = d.id
      WHERE d.status = 'completed'
      ORDER BY c.embedding <-> ?::vector
      LIMIT ?
    `,
      [JSON.stringify(embedding), limit],
    );

    return chunks.rows.map((chunk) => ({
      ...chunk,
      embedding: JSON.parse(chunk.embedding),
    }));
  }

  async searchSimilarWithDocumentInfo(embedding: number[], limit = 10) {
    const chunks = await this.knex.raw(
      `
      SELECT 
        c.*,
        d.filename,
        d.user_id,
        d.created_at as document_created_at
      FROM chunks c
      JOIN documents d ON c.document_id = d.id
      WHERE d.status = 'completed'
      ORDER BY c.embedding <-> ?::vector
      LIMIT ?
    `,
      [JSON.stringify(embedding), limit],
    );

    return chunks.rows.map((chunk) => ({
      ...chunk,
      embedding: JSON.parse(chunk.embedding),
    }));
  }
}
