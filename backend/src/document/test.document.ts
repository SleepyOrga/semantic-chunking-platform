import { NestFactory } from '@nestjs/core';
import { AppModule } from '../app.module';
import { DocumentService } from './document.service';
import { v4 as uuidv4 } from 'uuid';
import { Knex } from 'knex';

async function testDocumentService() {
  // Create NestJS application instance
  const app = await NestFactory.createApplicationContext(AppModule);
  
  // Get document service and database connection
  const documentService = app.get(DocumentService);
  const knex = app.get<Knex>('KNEX_CONNECTION');
  
  // Track user ID for cleanup
   let userId: string | undefined = undefined;
  
  try {
    console.log('===== Testing Document Service =====');
    
    // Create a test user directly in the database
    console.log('\nCreating test user...');
    userId = uuidv4();
    await knex('users').insert({
      id: userId,
      email: `test_${Date.now()}@example.com`,
      password_hash: '$2a$10$eDhqmQTXqVJ57DAYSQj9OeTQnX.2TnR5CAA9PoQ7nwvX/tn3rTJuK', // Hashed version of 'password123'
      full_name: 'Test User',
      created_at: new Date()
    });
    console.log(`Created test user with ID: ${userId}`);
    
    // 1. Create a document
    console.log('\n1. Creating document...');
    const documentId = await documentService.createDocument({
      user_id: userId, 
      filename: 'test-document.pdf',
      mimetype: 'application/pdf',
      size: 12345,
      path: '/uploads/test-document.pdf'
    });
    console.log(`Document created with ID: ${documentId}`);
    
    // Rest of your test remains the same
    // 2. Retrieve the document
    console.log('\n2. Retrieving document...');
    const document = await documentService.getDocumentById(documentId);
    console.log('Retrieved document:', document);
    
    // 3. Update the document status
    console.log('\n3. Updating document status...');
    await documentService.updateStatus({
      id: documentId,
      status: 'processing'
    });
    const updatedDocument = await documentService.getDocumentById(documentId);
    console.log('Updated document:', updatedDocument);
    
    // 4. Update document metadata
    console.log('\n4. Updating document metadata...');
    await documentService.updateDocument({
      id: documentId,
      filename: 'renamed-document.pdf',
      path: '/uploads/renamed-document.pdf'
    });
    const renamedDocument = await documentService.getDocumentById(documentId);
    console.log('Document after metadata update:', renamedDocument);
    
    // 5. Get documents by user ID
    console.log('\n5. Getting documents by user ID...');
    const userDocuments = await documentService.getDocumentsByUserId(userId);
    console.log(`Found ${userDocuments} documents for user:`);
    
    // 6. Get documents by status
    console.log('\n6. Getting documents by status...');
    const processingDocs = await documentService.getDocumentsByStatus('processing');
    console.log(`Found ${processingDocs.length} documents with 'processing' status`);
    
    // 7. Mark document as completed
    console.log('\n7. Marking document as completed...');
    await documentService.updateStatus({
      id: documentId,
      status: 'completed'
    });
    const completedDoc = await documentService.getDocumentById(documentId);
    console.log('Document after completion:', completedDoc);
    
    // 8. Get document stats (optional)
    console.log('\n8. Getting document statistics...');
    try {
      const stats = await documentService.getDocumentStats(userId);
      console.log('Document statistics:', stats);
    } catch (error) {
      console.log('Document stats not implemented or error:', error.message);
    }
    
    // 9. Delete the test document
    console.log('\n9. Deleting document...');
    await documentService.deleteDocument(documentId);
    console.log(`Document ${documentId} deleted successfully`);
    
    // 10. Verify deletion (should throw an error)
    console.log('\n10. Verifying deletion...');
    try {
      await documentService.getDocumentById(documentId);
      console.error('ERROR: Document still exists after deletion!');
    } catch (error) {
      console.log('Success: Document was properly deleted');
    }
    
    console.log('\nAll document tests completed successfully!');
  } catch (error) {
    console.error('Document test failed:', error);
  } finally {
    // Clean up - delete test user
    try {
      if (userId) {
        console.log('\nCleaning up test user...');
        await knex('users').where('id', userId).delete();
        console.log(`Test user ${userId} deleted`);
      }
    } catch (cleanupError) {
      console.error('Error during user cleanup:', cleanupError);
    }
    
    // Close the application
    await app.close();
  }
}

// Run the tests
testDocumentService()
  .then(() => console.log('Document testing complete'))
  .catch(err => console.error('Document testing failed:', err));