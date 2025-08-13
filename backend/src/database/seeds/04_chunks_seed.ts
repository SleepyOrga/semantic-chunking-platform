// src/database/seeds/03_chunks_seed.ts
import { Knex } from 'knex';

export async function seed(knex: Knex): Promise<void> {
  // Deletes ALL existing entries
  await knex('chunks').del();

  // Generate sample embeddings (1536 dimensions for OpenAI embeddings)
  const generateSampleEmbedding = () => {
    // Create a 1536-dimensional vector with random values between -1 and 1
    return JSON.stringify(Array(1536).fill(0).map(() => Math.random() * 2 - 1));
  };
  
  // Create test chunks with hardcoded UUIDs
  const chunks = [
    // Chunks for sample_report.pdf
    {
      id: "d85b0ad8-724b-4416-98dd-45c0412f0aa2",
      document_id: "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      chunk_index: 0,
      content: "Executive Summary: This report analyzes the financial performance of XYZ Corporation for the fiscal year 2023. The company showed strong growth in key markets while maintaining operational efficiency.",
      embedding: generateSampleEmbedding(),
      tags: ['executive-summary', 'financial', '2023'],
      created_at: new Date()
    },
    {
      id: "f2c336c4-5a6f-4a92-a454-0c3c11f9bd54",
      document_id: "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      chunk_index: 1,
      content: "Financial Highlights: Revenue increased by 12% to $125M. EBITDA margin improved to 28% from 25% in the previous year. Net income rose by 15% to $32M.",
      embedding: generateSampleEmbedding(),
      tags: ['financial-highlights', 'revenue', 'profit'],
      created_at: new Date()
    },
    
    // Additional chunks with similar structure...
  ];

  // Log the chunks
  console.log('Seeded chunks:');
  console.log(`✅ Created ${chunks.length} chunks for ${new Set(chunks.map(c => c.document_id)).size} documents`);

  // Insert chunks
  await knex('chunks').insert(chunks);
  
  console.log(`✅ Successfully inserted ${chunks.length} chunks`);
}