import { Knex } from 'knex';

export async function up(knex: Knex): Promise<void> {
  await knex.schema.createTable('chunks', (table) => {
    table.uuid('id').primary().defaultTo(knex.raw('uuid_generate_v4()'));
    table.uuid('document_id').notNullable();
    table.integer('chunk_index').notNullable()
      .comment('Sequential index of chunk within document');
    table.text('content').notNullable();
    table.specificType('embedding', 'vector(1536)')
      .comment('OpenAI embedding vector with 1536 dimensions');
    table.timestamp('created_at').defaultTo(knex.fn.now()).notNullable();
    
    // Foreign key constraint
    table.foreign('document_id').references('id').inTable('documents').onDelete('CASCADE');
    
    // Indexes
    table.index('document_id');
    table.index(['document_id', 'chunk_index']);
    table.unique(['document_id', 'chunk_index']); // Ensure unique chunk_index per document
    
    // Vector similarity search index (using HNSW algorithm)
    // This will be created after the table is created
  });
  
  // Create vector index for similarity search
  await knex.raw(`
    CREATE INDEX IF NOT EXISTS chunks_embedding_idx 
    ON chunks USING hnsw (embedding vector_cosine_ops)
  `);
  
  console.log('Chunks table created with vector index');
}

export async function down(knex: Knex): Promise<void> {
  await knex.schema.dropTableIfExists('chunks');
  console.log('Chunks table dropped');
}