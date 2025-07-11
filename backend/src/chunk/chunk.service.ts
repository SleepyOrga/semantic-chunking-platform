import { Injectable } from '@nestjs/common';
import { ChunkRepository } from '../repositories/chunk.repository';
import { DocumentRepository } from '../repositories/document.repository';
import { AddChunkDto, UpdateChunkDto, SimilaritySearchDto } from '../dto/chunk.dto';

@Injectable()
export class ChunkService {
  constructor(
    private readonly chunkRepository: ChunkRepository,
    private readonly documentRepository: DocumentRepository,
  ) {}

  async addChunk(data: AddChunkDto): Promise<string> {
    try {
      // Check if document exists
      const documentExists = await this.documentRepository.exists(data.document_id);
      if (!documentExists) {
        throw new Error(`Document with ID ${data.document_id} not found`);
      }
      
      const chunkId = await this.chunkRepository.create(data);
      
      console.log(`Chunk added successfully with ID: ${chunkId}`);
      return chunkId;
    } catch (error) {
      console.error(`Failed to add chunk to document ${data.document_id}:`, error);
      throw new Error(`Failed to add chunk: ${error.message}`);
    }
  }

  async getChunksByDocumentId(documentId: string) {
    try {
      // Check if document exists
      const documentExists = await this.documentRepository.exists(documentId);
      if (!documentExists) {
        throw new Error(`Document with ID ${documentId} not found`);
      }
      
      return await this.chunkRepository.findByDocumentId(documentId);
    } catch (error) {
      console.error(`Failed to get chunks for document ${documentId}:`, error);
      throw error;
    }
  }

  async getChunkById(id: string) {
    try {
      const chunk = await this.chunkRepository.findById(id);
      
      if (!chunk) {
        throw new Error(`Chunk with ID ${id} not found`);
      }
      
      return chunk;
    } catch (error) {
      console.error(`Failed to get chunk ${id}:`, error);
      throw error;
    }
  }

  async updateChunk(data: UpdateChunkDto): Promise<void> {
    try {
      const exists = await this.chunkRepository.exists(data.id);
      if (!exists) {
        throw new Error(`Chunk with ID ${data.id} not found`);
      }
      
      const { id, ...updateData } = data;
      await this.chunkRepository.update(id, updateData);
      
      console.log(`Chunk ${id} updated successfully`);
    } catch (error) {
      console.error(`Failed to update chunk ${data.id}:`, error);
      throw error;
    }
  }

  async deleteChunk(id: string): Promise<void> {
    try {
      const exists = await this.chunkRepository.exists(id);
      if (!exists) {
        throw new Error(`Chunk with ID ${id} not found`);
      }
      
      await this.chunkRepository.delete(id);
      
      console.log(`Chunk ${id} deleted successfully`);
    } catch (error) {
      console.error(`Failed to delete chunk ${id}:`, error);
      throw error;
    }
  }

  async deleteChunksByDocumentId(documentId: string): Promise<void> {
    try {
      // Check if document exists
      const documentExists = await this.documentRepository.exists(documentId);
      if (!documentExists) {
        throw new Error(`Document with ID ${documentId} not found`);
      }
      
      await this.chunkRepository.deleteByDocumentId(documentId);
      
      console.log(`All chunks for document ${documentId} deleted successfully`);
    } catch (error) {
      console.error(`Failed to delete chunks for document ${documentId}:`, error);
      throw error;
    }
  }

  async searchSimilarChunks(data: SimilaritySearchDto) {
    try {
      const { embedding, limit = 10 } = data;
      return await this.chunkRepository.searchSimilarWithDocumentInfo(embedding, limit);
    } catch (error) {
      console.error('Failed to search similar chunks:', error);
      throw new Error(`Failed to search similar chunks: ${error.message}`);
    }
  }
}