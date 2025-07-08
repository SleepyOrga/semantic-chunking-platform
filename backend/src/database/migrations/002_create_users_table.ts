import { Knex } from 'knex';

export async function up(knex: Knex): Promise<void> {
  await knex.schema.createTable('users', (table) => {
    table.uuid('id').primary().defaultTo(knex.raw('uuid_generate_v4()'));
    table.string('email', 255).unique().notNullable();
    table.string('password_hash', 255).notNullable();
    table.string('full_name', 255).notNullable();
    table.timestamp('created_at').defaultTo(knex.fn.now()).notNullable();
    
    // Indexes
    table.index('email');
    table.index('created_at');
  });
  
  console.log('Users table created');
}

export async function down(knex: Knex): Promise<void> {
  await knex.schema.dropTableIfExists('users');
  console.log('Users table dropped');
}