import { Knex } from 'knex';

export async function up(knex: Knex): Promise<void> {
  await knex.schema.createTable('documents', (table) => {
    table.uuid('id').primary().defaultTo(knex.raw('uuid_generate_v4()'));
    table.uuid('user_id').notNullable();
    table.string('filename', 255).notNullable();
    table.string('mimetype', 100).notNullable();
    table.integer('size').notNullable();
    table.string('path', 500).comment('File storage path on disk or cloud storage');
    table.string('status', 20).defaultTo('pending').notNullable()
      .comment('Document processing status: pending, processing, completed, failed');
    table.text('error_message').nullable();
    table.timestamp('created_at').defaultTo(knex.fn.now()).notNullable();
    
    // Foreign key constraint
    table.foreign('user_id').references('id').inTable('users').onDelete('CASCADE');
    
    // Indexes
    table.index('user_id');
    table.index('status');
    table.index('created_at');
    table.index(['user_id', 'created_at']);
  });
  
  console.log('Documents table created');
}

export async function down(knex: Knex): Promise<void> {
  await knex.schema.dropTableIfExists('documents');
  console.log('Documents table dropped');
}