import { NestFactory } from '@nestjs/core';
import { AppModule } from '../app.module';
import { DocumentService } from '../document/document.service';
import { ChunkService } from './chunk.service';
import { v4 as uuidv4 } from 'uuid';
import { Knex } from 'knex';

// ANSI color codes for better test output visibility
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
};

async function testChunkService() {
  // Create NestJS application instance
  const app = await NestFactory.createApplicationContext(AppModule);

  // Get services and database connection
  const documentService = app.get(DocumentService);
  const chunkService = app.get(ChunkService);
  const knex = app.get<Knex>('KNEX_CONNECTION');

  // Track IDs for cleanup
  let userId: string | undefined = undefined;
  let documentId: string | undefined = undefined;
  let chunkId1: string | undefined = undefined;
  let chunkId2: string | undefined = undefined;
  // Create some test tags
  const testTags = ['test-tag', 'important', 'technical'];

  // Test tracking
  const testResults = {
    total: 0,
    passed: 0,
    failed: 0,
    skipped: 0,
    errors: [] as string[],
  };

  function logTestResult(testName: string, passed: boolean, error?: any) {
    testResults.total++;
    if (passed) {
      testResults.passed++;
      console.log(`${colors.green}✅ PASS:${colors.reset} ${testName}`);
    } else {
      testResults.failed++;
      console.log(`${colors.red}❌ FAIL:${colors.reset} ${testName}`);
      const errorMsg = error ? `${error.message || error}` : 'Unknown error';
      testResults.errors.push(`${testName}: ${errorMsg}`);
      console.error(`   ${colors.red}Error:${colors.reset} ${errorMsg}`);
    }
  }

  function logTestSkipped(testName: string, reason: string) {
    testResults.total++;
    testResults.skipped++;
    console.log(
      `${colors.yellow}⏭️ SKIP:${colors.reset} ${testName} (${reason})`,
    );
  }

  try {
    console.log(
      `${colors.cyan}===== Testing Chunk Service =====${colors.reset}`,
    );

    // Create test tags in the database
    console.log('\nCreating test tags...');
    try {
      for (const tagName of testTags) {
        await knex('tags').insert({
          name: tagName,
          created_at: new Date(),
        });
      }
      console.log(`Created test tags: ${testTags.join(', ')}`);
      logTestResult('Create test tags', true);
    } catch (error) {
      logTestResult('Create test tags', false, error);
      // We can continue even if tag creation fails
    }

    // Create a test user directly in the database
    console.log('\nCreating test user...');
    try {
      userId = uuidv4();
      await knex('users').insert({
        id: userId,
        email: `test_${Date.now()}@example.com`,
        password_hash:
          '$2a$10$eDhqmQTXqVJ57DAYSQj9OeTQnX.2TnR5CAA9PoQ7nwvX/tn3rTJuK', // 'password123'
        full_name: 'Test User',
        created_at: new Date(),
      });
      console.log(`Created test user with ID: ${userId}`);
      logTestResult('Create test user', true);
    } catch (error) {
      logTestResult('Create test user', false, error);
      // If we can't create a user, we should stop the tests
      throw new Error('Failed to create test user, cannot continue tests');
    }

    // Create a test document
    console.log('\nCreating test document...');
    try {
      documentId = await documentService.createDocument({
        user_id: userId,
        filename: 'test-document-for-chunks.pdf',
        mimetype: 'application/pdf',
        size: 12345,
        path: '/uploads/test-document-for-chunks.pdf',
      });
      console.log(`Created test document with ID: ${documentId}`);

      // Mark document as processing
      await documentService.updateStatus({
        id: documentId,
        status: 'processing',
      });
      logTestResult('Create test document', true);
    } catch (error) {
      logTestResult('Create test document', false, error);
      // If we can't create a document, we should stop the tests
      throw new Error('Failed to create test document, cannot continue tests');
    }

    //--------------------------------------------------
    // CHUNK TESTS
    //--------------------------------------------------
    console.log(`\n${colors.cyan}===== CHUNK TESTS =====${colors.reset}`);

    // 1. Add first chunk to the document
    console.log('\n1. Adding first chunk...');
    try {
      chunkId1 = await chunkService.addChunk({
        document_id: documentId,
        chunk_index: 0,
        content: 'This is the first chunk of text from the document.',
        embedding: new Array(1536).fill(0).map(() => Math.random()),
      });
      console.log(`First chunk created with ID: ${chunkId1}`);
      logTestResult('1. Add first chunk', true);
    } catch (error) {
      logTestResult('1. Add first chunk', false, error);
    }

    // 2. Add second chunk to the document with tags
    console.log('\n2. Adding second chunk with tags...');
    try {
      chunkId2 = await chunkService.addChunk({
        document_id: documentId,
        chunk_index: 1,
        content: 'This is the second chunk of text from the document.',
        embedding: new Array(1536).fill(0).map(() => Math.random()),
        tags: [testTags[0], testTags[1]] // Add two tags
      });
      console.log(`Second chunk created with ID: ${chunkId2}`);
      logTestResult('2. Add second chunk with tags', true);
    } catch (error) {
      logTestResult('2. Add second chunk with tags', false, error);
    }

    // 3. Get a specific chunk
    console.log('\n3. Retrieving specific chunk...');
    try {
      if (!chunkId1) {
        logTestSkipped(
          '3. Retrieve specific chunk',
          'First chunk creation failed',
        );
      } else {
        const chunk = await chunkService.getChunkById(chunkId1);
        console.log('Retrieved chunk:', {
          id: chunk.id,
          document_id: chunk.document_id,
          chunk_index: chunk.chunk_index,
          content: chunk.content,
          embedding_length: chunk.embedding ? chunk.embedding.length : 0,
          tags: chunk.tags || []
        });
        logTestResult('3. Retrieve specific chunk', true);
      }
    } catch (error) {
      logTestResult('3. Retrieve specific chunk', false, error);
    }

    // 4. Get all chunks for the document
    console.log('\n4. Retrieving all chunks for document...');
    try {
      const chunks = await chunkService.getChunksByDocumentId(documentId);
      console.log(
        `Retrieved ${chunks.length} chunks for document ${documentId}`,
      );
      chunks.forEach((chunk, index) => {
        console.log(
          `[${index}] Chunk #${chunk.chunk_index}: ${chunk.content.substring(0, 30)}...`,
        );
      });
      // Test should pass if we retrieved the expected number of chunks
      const expectedChunks = (chunkId1 ? 1 : 0) + (chunkId2 ? 1 : 0);
      logTestResult(
        '4. Get all chunks for document',
        chunks.length === expectedChunks,
      );
    } catch (error) {
      logTestResult('4. Get all chunks for document', false, error);
    }

    // 5. Update a chunk
    console.log('\n5. Updating chunk content and embedding...');
    try {
      if (!chunkId1) {
        logTestSkipped('5. Update chunk', 'First chunk creation failed');
      } else {
        await chunkService.updateChunk({
          id: chunkId1,
          content: 'This is the UPDATED first chunk of text.',
          embedding: new Array(1536).fill(0).map(() => Math.random()),
        });
        const updatedChunk = await chunkService.getChunkById(chunkId1);
        console.log('Updated chunk content:', updatedChunk.content);
        // Test passes if content was updated successfully
        const contentUpdated =
          updatedChunk.content === 'This is the UPDATED first chunk of text.';
        logTestResult('5. Update chunk content and embedding', contentUpdated);
      }
    } catch (error) {
      logTestResult('5. Update chunk content and embedding', false, error);
    }

    // 6. Update tags for a chunk (previously was tag_embedding)
    console.log('\n6. Adding tags to a chunk...');
    try {
      if (!chunkId1) {
        logTestSkipped(
          '6. Add tags to chunk',
          'First chunk creation failed',
        );
      } else {
        await chunkService.setChunkTags(chunkId1, { tags: [testTags[0], testTags[2]] });
        
        const taggedChunk = await chunkService.getChunkById(chunkId1);
        console.log(
          'Chunk now has tags:',
          taggedChunk.tags || []
        );
        const hasTags = Array.isArray(taggedChunk.tags) && taggedChunk.tags.length > 0;
        logTestResult('6. Add tags to chunk', hasTags);
      }
    } catch (error) {
      logTestResult('6. Add tags to chunk', false, error);
    }

    // 7. Search similar chunks by content
    console.log('\n7. Searching similar chunks by content...');
    try {
      // Generate a random embedding vector for testing
      const testEmbedding = new Array(1536).fill(0).map(() => Math.random());
      const similarChunks = await chunkService.searchSimilarChunks({
        embedding: testEmbedding,
        limit: 5,
      });
      console.log(`Found ${similarChunks.length} similar chunks by content`);
      similarChunks.forEach((result, i) => {
        console.log(`  [${i}] ${result.content.substring(0, 30)}...`);
      });
      logTestResult('7. Search similar chunks by content', true);
    } catch (err) {
      console.log('Search by content similarity error:', err.message);
      logTestResult('7. Search similar chunks by content', false, err);
    }

    // 8. Search chunks by tags (previously was tag embedding)
    console.log('\n8. Searching chunks by tags...');
    try {
      const tagSearchResults = await chunkService.searchByTags({
        tags: [testTags[0]], // Search for chunks with this tag
        matchAll: false,
        limit: 5
      });
      console.log(`Found ${tagSearchResults.chunks.length} chunks with specified tags`);
      tagSearchResults.chunks.forEach((result, i) => {
        console.log(`  [${i}] ${result.content.substring(0, 30)}... Tags: ${result.tags?.join(', ') || 'none'}`);
      });
      logTestResult('8. Search chunks by tags', true);
    } catch (err) {
      console.log('Search by tags error:', err.message);
      logTestResult('8. Search chunks by tags', false, err);
    }

    let chunkIdTest10 = chunkId1; // Store before deletion

    // 9. Delete a specific chunk
    console.log('\n9. Deleting first chunk...');
    try {
      if (!chunkId1) {
        logTestSkipped(
          '9. Delete specific chunk',
          'First chunk creation failed',
        );
      } else {
        await chunkService.deleteChunk(chunkId1);
        console.log(`Chunk ${chunkId1} deleted successfully`);
        chunkId1 = undefined; // Mark as deleted
        logTestResult('9. Delete specific chunk', true);
      }
    } catch (error) {
      logTestResult('9. Delete specific chunk', false, error);
    }

    // 10. Verify first chunk is deleted
    console.log('\n10. Verifying first chunk deletion...');
    try {
      let deletionVerified = false;

      // Store the deleted chunk ID before setting it to undefined
      const deletedChunkId = chunkIdTest10;

      if (!deletedChunkId) {
        logTestSkipped('10. Verify chunk deletion', 'No chunk ID to verify');
      } else {
        try {
          // Use the actual UUID that was deleted, not the string 'deleted'
          await chunkService.getChunkById(deletedChunkId);
          console.error('ERROR: Chunk still exists after deletion!');
        } catch (error) {
          console.log('Success: Chunk was properly deleted');
          deletionVerified = true;
        }
        logTestResult('10. Verify chunk deletion', deletionVerified);
      }
    } catch (error) {
      logTestResult('10. Verify chunk deletion', false, error);
    }

    // 11. Delete all chunks for the document
    console.log('\n11. Deleting all remaining chunks for document...');
    try {
      await chunkService.deleteChunksByDocumentId(documentId);
      chunkId2 = undefined; // Mark as deleted
      logTestResult('11. Delete all document chunks', true);
    } catch (error) {
      logTestResult('11. Delete all document chunks', false, error);
    }

    // 12. Verify all chunks are deleted
    console.log('\n12. Verifying all chunks are deleted...');
    try {
      const remainingChunks =
        await chunkService.getChunksByDocumentId(documentId);
      if (remainingChunks.length === 0) {
        console.log('Success: All chunks were properly deleted');
        logTestResult('12. Verify all chunks deleted', true);
      } else {
        console.error(`ERROR: ${remainingChunks.length} chunks still exist!`);
        logTestResult(
          '12. Verify all chunks deleted',
          false,
          new Error(`${remainingChunks.length} chunks still exist`),
        );
      }
    } catch (error) {
      logTestResult('12. Verify all chunks deleted', false, error);
    }

    // Mark document as completed
    try {
      await documentService.updateStatus({
        id: documentId,
        status: 'completed',
      });
    } catch (error) {
      console.error('Failed to mark document as completed:', error);
    }

    // Print test summary
    const success = testResults.failed === 0;
    console.log('\n' + '-'.repeat(50));
    console.log(`${colors.cyan}TEST SUMMARY${colors.reset}`);
    console.log('-'.repeat(50));
    console.log(`Total Tests:  ${testResults.total}`);
    console.log(
      `${colors.green}Passed:      ${testResults.passed}${colors.reset}`,
    );
    console.log(
      `${colors.red}Failed:      ${testResults.failed}${colors.reset}`,
    );
    console.log(
      `${colors.yellow}Skipped:     ${testResults.skipped}${colors.reset}`,
    );
    console.log('-'.repeat(50));

    if (testResults.failed > 0) {
      console.log(`${colors.red}Failed Tests:${colors.reset}`);
      testResults.errors.forEach((error, index) => {
        console.log(`  ${index + 1}. ${error}`);
      });
      console.log('-'.repeat(50));
    }

    // Final status
    if (success) {
      console.log(
        `${colors.green}FINAL STATUS: ALL TESTS PASSED${colors.reset}`,
      );
    } else {
      console.log(
        `${colors.red}FINAL STATUS: ${testResults.failed} TESTS FAILED${colors.reset}`,
      );
    }

    return success;
  } catch (error) {
    console.error(`${colors.red}Chunk test failed:${colors.reset}`, error);
    return false;
  } finally {
    // Clean up - delete test resources
    try {
      console.log('\nCleaning up test resources...');

      // Delete remaining chunks if any
      if (chunkId1) {
        console.log(`- Cleaning up chunk ${chunkId1}...`);
        await chunkService.deleteChunk(chunkId1);
      }

      if (chunkId2) {
        console.log(`- Cleaning up chunk ${chunkId2}...`);
        await chunkService.deleteChunk(chunkId2);
      }

      // Delete document
      if (documentId) {
        console.log(`- Cleaning up document ${documentId}...`);
        await documentService.deleteDocument(documentId);
      }

      // Delete user
      if (userId) {
        console.log(`- Cleaning up user ${userId}...`);
        await knex('users').where('id', userId).delete();
      }
      
      // Delete test tags
      console.log(`- Cleaning up test tags...`);
      await knex('tags').whereIn('name', testTags).delete();

      console.log('All test resources cleaned up');
    } catch (cleanupError) {
      console.error('Error during cleanup:', cleanupError);
    }

    // Close the application
    await app.close();
  }
}

// Run the tests
testChunkService()
  .then((success) => {
    console.log(`\nChunk testing ${success ? 'PASSED ✅' : 'FAILED ❌'}`);
    // Set exit code based on test success/failure
    process.exit(success ? 0 : 1);
  })
  .catch((err) => {
    console.error('Chunk testing failed with an exception:', err);
    process.exit(1);
  });