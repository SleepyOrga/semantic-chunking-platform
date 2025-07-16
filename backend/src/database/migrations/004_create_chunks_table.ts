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
    // Replace tag_embedding with tags array
    table.specificType('tags', 'TEXT[]')
      .nullable()
      .comment('Array of tag names referencing tags table');
    table.timestamp('created_at').defaultTo(knex.fn.now()).notNullable();
    
    // Foreign key constraint
    table.foreign('document_id').references('id').inTable('documents').onDelete('CASCADE');
    
    // Indexes
    table.index('document_id');
    table.index(['document_id', 'chunk_index']);
    table.unique(['document_id', 'chunk_index']); // Ensure unique chunk_index per document
  });
  
  // Create vector index for content embedding similarity search
  await knex.raw(`
    CREATE INDEX IF NOT EXISTS chunks_embedding_idx 
    ON chunks USING hnsw (embedding vector_cosine_ops)
  `);
  
  // Create GIN index for tags array
  await knex.raw(`
    CREATE INDEX IF NOT EXISTS chunks_tags_idx 
    ON chunks USING GIN (tags)
  `);
  
  // Create a trigger to validate tags exist in the tags table
  await knex.raw(`
    CREATE OR REPLACE FUNCTION validate_chunk_tags()
    RETURNS TRIGGER AS $$
    DECLARE
      invalid_tags TEXT[];
    BEGIN
      IF NEW.tags IS NOT NULL THEN
        -- Find any tags in the array that don't exist in the tags table
        SELECT ARRAY_AGG(t)
        INTO invalid_tags
        FROM UNNEST(NEW.tags) AS t
        WHERE NOT EXISTS (
          SELECT 1 FROM tags WHERE name = t
        );
        
        -- If invalid tags were found, raise an error
        IF invalid_tags IS NOT NULL AND array_length(invalid_tags, 1) > 0 THEN
          RAISE EXCEPTION 'Tags not found in tags table: %', invalid_tags;
        END IF;
      END IF;
      
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
  `);
  
  await knex.raw(`
    CREATE TRIGGER validate_chunk_tags_trigger
    BEFORE INSERT OR UPDATE ON chunks
    FOR EACH ROW
    EXECUTE FUNCTION validate_chunk_tags();
  `);
  
  console.log('Chunks table created with content embedding vector index and tags array');
}

export async function down(knex: Knex): Promise<void> {
  // Drop the trigger and function first
  await knex.raw(`
    DROP TRIGGER IF EXISTS validate_chunk_tags_trigger ON chunks;
    DROP FUNCTION IF EXISTS validate_chunk_tags();
  `);
  
  await knex.schema.dropTableIfExists('chunks');
  console.log('Chunks table dropped');
}