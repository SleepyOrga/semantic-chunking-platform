import { Injectable, Inject, OnModuleDestroy, Logger } from '@nestjs/common';
import { Knex } from 'knex';

@Injectable()
export class KnexService implements OnModuleDestroy {
  private readonly logger = new Logger(KnexService.name);

  constructor(@Inject('KNEX_CONNECTION') private readonly knex: Knex) {}

  getKnex(): Knex {
    return this.knex;
  }

  async onModuleDestroy() {
    try {
      await this.knex.destroy();
      this.logger.log('Knex connection closed');
    } catch (error) {
      this.logger.error('Error closing Knex connection:', error);
    }
  }

  // Helper methods for common operations
  async transaction<T>(callback: (trx: Knex.Transaction) => Promise<T>): Promise<T> {
    return await this.knex.transaction(callback);
  }

  async healthCheck(): Promise<boolean> {
    try {
      await this.knex.raw('SELECT 1');
      return true;
    } catch (error) {
      this.logger.error('Health check failed:', error);
      return false;
    }
  }

  async runMigrations(): Promise<void> {
    try {
      await this.knex.migrate.latest();
      this.logger.log('Migrations completed successfully');
    } catch (error) {
      this.logger.error('Migration failed:', error);
      throw error;
    }
  }

  async rollbackMigration(): Promise<void> {
    try {
      await this.knex.migrate.rollback();
      this.logger.log('Migration rollback completed');
    } catch (error) {
      this.logger.error('Migration rollback failed:', error);
      throw error;
    }
  }
}