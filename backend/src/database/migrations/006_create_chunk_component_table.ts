import { Knex } from 'knex';

export async function up(knex: Knex): Promise<void> {
  await knex.schema.createTable('chunk_components', (table) => {
    table.uuid('id').primary().defaultTo(knex.raw('uuid_generate_v4()'));
    table.uuid('chunk_id').notNullable()
      .comment('Reference to parent chunk');
    table.integer('component_index').notNullable()
      .comment('Sequential index of component within chunk');
    table.text('content').notNullable()
      .comment('Sub-content of the chunk component');
    table.specificType('embedding', 'vector(1024)')
      .comment('OpenAI embedding vector for this component');
    table.timestamp('created_at').defaultTo(knex.fn.now()).notNullable();
    
    // Foreign key constraint
    table.foreign('chunk_id').references('id').inTable('chunks').onDelete('CASCADE');
    
    // Indexes
    table.index('chunk_id');
    table.index(['chunk_id', 'component_index']);
    table.unique(['chunk_id', 'component_index']); // Ensure unique component_index per chunk
  });
  
  // Create vector index for component embedding similarity search
  await knex.raw(`
    CREATE INDEX IF NOT EXISTS chunk_components_embedding_idx 
    ON chunk_components USING hnsw (embedding vector_cosine_ops)
  `);
  
  console.log('Chunk components table created with vector index');
}

export async function down(knex: Knex): Promise<void> {
  await knex.schema.dropTableIfExists('chunk_components');
  console.log('Chunk components table dropped');
}