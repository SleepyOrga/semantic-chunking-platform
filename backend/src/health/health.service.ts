import { Injectable, Inject } from '@nestjs/common';
import { Knex } from 'knex';

@Injectable()
export class HealthService {
  constructor(@Inject('KNEX_CONNECTION') private readonly knex: Knex) {}

  async checkHealth(): Promise<{
    status: string;
    message: string;
    chunksCount?: number;
    documentsCount?: number;
    usersCount?: number;
    dbStatus: boolean;
    timestamp: string;
  }> {
    try {
      // Check database connection by querying basic stats
      const [chunksCount] = await this.knex('chunks').count('id as count');
      const [documentsCount] = await this.knex('documents').count('id as count');
      const [usersCount] = await this.knex('users').count('id as count');
      
      // Count completed documents
      const [completedDocuments] = await this.knex('documents')
        .where('status', 'completed')
        .count('id as count');

      return {
        status: 'healthy',
        message: `API is running. Database connected successfully. Found ${chunksCount.count} chunks, ${documentsCount.count} documents (${completedDocuments.count} completed), ${usersCount.count} users.`,
        chunksCount: Number(chunksCount.count),
        documentsCount: Number(documentsCount.count), 
        usersCount: Number(usersCount.count),
        dbStatus: true,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      console.error('Health check failed:', error);
      return {
        status: 'unhealthy',
        message: `Database connection failed: ${error.message}`,
        dbStatus: false,
        timestamp: new Date().toISOString(),
      };
    }
  }
}