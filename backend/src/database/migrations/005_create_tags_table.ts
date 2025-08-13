import { Knex } from 'knex';

export async function up(knex: Knex): Promise<void> {
  await knex.schema.createTable('tags', (table) => {
    table.increments('id').primary();
    table.string('name', 255).notNullable().unique();
    table.timestamp('created_at').defaultTo(knex.fn.now()).notNullable();
    
    // Index for faster lookups
    table.index('name');
  });
  
  console.log('Tags table created');
}

export async function down(knex: Knex): Promise<void> {
  await knex.schema.dropTableIfExists('tags');
  console.log('Tags table dropped');
}