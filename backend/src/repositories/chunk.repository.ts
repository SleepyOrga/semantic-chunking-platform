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
    // First insert the record without embeddings
    const [chunk] = await this.knex('chunks')
      .insert({
        document_id: data.document_id,
        chunk_index: data.chunk_index,
        content: data.content,
      })
      .returning('id');

    // Then update with properly formatted embeddings
    if (data.embedding) {
      await this.knex.raw(
        `UPDATE chunks SET embedding = ?::vector WHERE id = ?`,
        [`[${data.embedding.join(',')}]`, chunk.id],
      );
    }

    if (data.tag_embedding) {
      await this.knex.raw(
        `UPDATE chunks SET tag_embedding = ?::vector WHERE id = ?`,
        [`[${data.tag_embedding.join(',')}]`, chunk.id],
      );
    }

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
    const updateData: any = {};

    if (data.content !== undefined) updateData.content = data.content;

    // First do the regular update
    if (Object.keys(updateData).length > 0) {
      await this.knex('chunks').where({ id }).update(updateData);
    }

    // Handle embedding updates with proper PostgreSQL vector formatting
    if (data.embedding !== undefined) {
      // Format the vector for PostgreSQL
      await this.knex.raw(
        `UPDATE chunks SET embedding = ?::vector WHERE id = ?`,
        [`[${data.embedding.join(',')}]`, id],
      );
    }

    // Handle tag_embedding updates with proper PostgreSQL vector formatting
    if (data.tag_embedding !== undefined) {
      // Format the vector properly for PostgreSQL
      await this.knex.raw(
        `UPDATE chunks SET tag_embedding = ?::vector WHERE id = ?`,
        [`[${data.tag_embedding.join(',')}]`, id],
      );
    }
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
  async searchSimilarByTag(
    tagEmbedding: number[],
    limit: number = 10,
  ): Promise<ChunkEntity[]> {
    // Convert embedding to Postgres vector format
    const tagEmbeddingStr = `[${tagEmbedding.join(',')}]`;

    const results = await this.knex.raw(
      `
    SELECT c.*, d.filename, d.mimetype
    FROM chunks c
    JOIN documents d ON c.document_id = d.id
    WHERE c.tag_embedding IS NOT NULL
    ORDER BY c.tag_embedding <=> ?::vector
    LIMIT ?
  `,
      [tagEmbeddingStr, limit],
    );

    return results.rows.map((row) => ({
      ...row,
      embedding: Array.isArray(row.embedding) ? row.embedding : [],
      tag_embedding: Array.isArray(row.tag_embedding) ? row.tag_embedding : [],
    }));
  }
}
