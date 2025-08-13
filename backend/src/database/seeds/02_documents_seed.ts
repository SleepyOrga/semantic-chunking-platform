import { Knex } from 'knex';

export async function seed(knex: Knex): Promise<void> {
  // Deletes ALL existing entries
  await knex('documents').del();
  
  // Create test documents with hardcoded UUIDs
  const documents = [
    {
      id: "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      user_id: "05b207af-8ea7-4a72-8c37-f5723303d01e", // Admin user
      filename: "sample_report.pdf",
      mimetype: "application/pdf",
      path: "uploads/admin/sample_report.pdf",
      size: 245678,
      status: "processed",
      created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) // 7 days ago
    },
    {
      id: "6ec0bd7f-11c0-43da-975e-2a8ad9ebae0b",
      user_id: "7c11e1ce-1144-42bf-92d8-59392314e0c0", // User 1
      filename: "financial_data.xlsx",
      mimetype: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      path: "uploads/user1/financial_data.xlsx",
      size: 128456,
      status: "processed",
      created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000) // 5 days ago
    },
    {
      id: "3f333df6-90a4-4fda-8dd3-9485d27cee36",
      user_id: "7c11e1ce-1144-42bf-92d8-59392314e0c0", // User 1
      filename: "presentation.pptx",
      mimetype: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      path: "uploads/user1/presentation.pptx",
      size: 345821,
      status: "processed",
      created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000) // 3 days ago
    },
    {
      id: "670c07bd-f6d6-4734-a18b-62d8fddf8e37",
      user_id: "3b9ad953-7245-42e8-a8c8-8ff1a5986f89", // User 2
      filename: "research_paper.docx",
      mimetype: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      path: "uploads/user2/research_paper.docx",
      size: 567234,
      status: "processed",
      created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000) // 2 days ago
    },
    {
      id: "55c9e1ab-3095-4a48-b541-cab675d356d5",
      user_id: "d4f25424-7b17-4b88-b9c4-20ea66655a05", // Demo user
      filename: "demo_document.pdf",
      mimetype: "application/pdf",
      path: "uploads/demo/demo_document.pdf",
      size: 198432,
      status: "processed",
      created_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000) // 1 day ago
    }
  ];

  // Log the documents
  console.log('Seeded documents:');
  documents.forEach(doc => {
    console.log(`- ${doc.filename} (User: ${doc.user_id}): ${doc.id}`);
  });

  // Insert documents
  await knex('documents').insert(documents);
  
  console.log(`✅ Successfully inserted ${documents.length} documents`);
}