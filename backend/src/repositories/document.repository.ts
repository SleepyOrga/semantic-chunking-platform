import { Injectable, Inject } from '@nestjs/common';
import { Knex } from 'knex';
import {
  DocumentEntity,
  CreateDocumentData,
  UpdateDocumentData,
} from '../entities/document.entity';

@Injectable()
export class DocumentRepository {
  constructor(@Inject('KNEX_CONNECTION') private readonly knex: Knex) {}

  async create(data: CreateDocumentData): Promise<string> {
    const [document] = await this.knex('documents')
      .insert({
        user_id: data.user_id,
        filename: data.filename,
        mimetype: data.mimetype,
        size: data.size,
        path: data.path,
        status: data.status || 'pending',
        error_message: data.error_message,
      })
      .returning('id');

    return document.id;
  }

  async findById(id: string): Promise<DocumentEntity | null> {
    return await this.knex('documents').where('id', id).first();
  }

  async findByUserId(
    userId: string,
    limit = 50,
    offset = 0,
  ): Promise<DocumentEntity[]> {
    return await this.knex('documents')
      .where('user_id', userId)
      .orderBy('created_at', 'desc')
      .limit(limit)
      .offset(offset);
  }

  async findByStatus(
    status: string,
    limit = 50,
    offset = 0,
  ): Promise<DocumentEntity[]> {
    return await this.knex('documents')
      .where('status', status)
      .orderBy('created_at', 'asc')
      .limit(limit)
      .offset(offset);
  }

  async update(id: string, data: UpdateDocumentData): Promise<void> {
    await this.knex('documents').where('id', id).update(data);
  }

  async updateStatus(
    id: string,
    status: string,
    errorMessage?: string,
  ): Promise<void> {
    await this.knex('documents').where('id', id).update({
      status,
      error_message: errorMessage,
    });
  }

  async delete(id: string): Promise<void> {
    await this.knex('documents').where('id', id).del();
  }

  async exists(id: string): Promise<boolean> {
    try {
      const count = await this.knex('documents')
        .where('id', id)
        .count('id as count')
        .first();

      return count ? parseInt(count.count as string) > 0 : false;
    } catch (error) {
      console.error(`Error checking if document exists: ${error.message}`);
      return false;
    }
  }
  async getStats(userId?: string) {
    const query = this.knex('documents')
      .select('status')
      .count('* as count')
      .groupBy('status');

    if (userId) {
      query.where('user_id', userId);
    }

    return await query;
  }

  async countByUserId(userId: string): Promise<number> {
    try {
      const result = await this.knex('documents')
        .where('user_id', userId)
        .count('id as count')
        .first();

      return result ? parseInt(result.count as string) : 0;
    } catch (error) {
      console.error(`Error counting documents by user ID: ${error.message}`);
      return 0;
    }
  }
}
