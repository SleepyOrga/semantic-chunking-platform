// src/database/seeds/04_tags_seed.ts
import { Knex } from 'knex';

export async function seed(knex: Knex): Promise<void> {
  // Deletes ALL existing entries
  await knex('tags').del();

  // Create sample tags
  const tags = [
    { id: 1, name: 'executive-summary', created_at: new Date() },
    { id: 2, name: 'financial', created_at: new Date() },
    { id: 3, name: 'financial-highlights', created_at: new Date() },
    { id: 4, name: 'revenue', created_at: new Date() },
    { id: 5, name: 'profit', created_at: new Date() },
    { id: 6, name: '2023', created_at: new Date() },
    { id: 7, name: 'sales', created_at: new Date() },
    { id: 8, name: 'quarterly', created_at: new Date() },
    { id: 9, name: 'product-roadmap', created_at: new Date() },
    { id: 10, name: 'research', created_at: new Date() },
    { id: 11, name: 'abstract', created_at: new Date() },
    { id: 12, name: 'methodology', created_at: new Date() },
    { id: 13, name: 'semantic-search', created_at: new Date() },
    { id: 14, name: 'introduction', created_at: new Date() },
    { id: 15, name: 'benefits', created_at: new Date() },
  ];

  // Log the tags
  console.log('Seeded tags:');
  console.log(`✅ Created ${tags.length} tags`);

  // Insert tags
  await knex('tags').insert(tags);

  await knex.raw(`SELECT setval('tags_id_seq', (SELECT MAX(id) FROM tags));`);
  console.log('✅ Reset tags_id_seq to continue from highest ID');

  console.log(`✅ Successfully inserted ${tags.length} tags`);
}
