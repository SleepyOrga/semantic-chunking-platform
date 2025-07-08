import { Knex } from 'knex';

export async function up(knex: Knex): Promise<void> {
  // Enable UUID extension
  await knex.raw('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"');
  
  // Enable pgvector extension
  await knex.raw('CREATE EXTENSION IF NOT EXISTS "vector"');
  
  console.log('Extensions created: uuid-ossp, vector');
}

export async function down(knex: Knex): Promise<void> {
  // Note: Be careful when dropping extensions in production
  await knex.raw('DROP EXTENSION IF EXISTS "vector"');
  await knex.raw('DROP EXTENSION IF EXISTS "uuid-ossp"');
  
  console.log('Extensions dropped: vector, uuid-ossp');
}