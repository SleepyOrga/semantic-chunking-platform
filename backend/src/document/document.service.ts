import { Injectable } from '@nestjs/common';
import { DocumentRepository } from '../repositories/document.repository';
import { 
  CreateDocumentDto, 
  UpdateDocumentDto, 
  UpdateDocumentStatusDto,
  DocumentQuery
} from '../dto/document.dto';

@Injectable()
export class DocumentService {
  constructor(
    private readonly documentRepository: DocumentRepository,
  ) {}

  async createDocument(data: CreateDocumentDto): Promise<string> {
    try {
      const documentId = await this.documentRepository.create({
        ...data,
        status: 'pending',
      });
      
      console.log(`Document created successfully with ID: ${documentId}`);
      return documentId;
    } catch (error) {
      console.error('Failed to create document:', error);
      throw new Error(`Failed to create document: ${error.message}`);
    }
  }

  async getDocumentById(id: string) {
    try {
      const document = await this.documentRepository.findById(id);
      
      if (!document) {
        throw new Error(`Document with ID ${id} not found`);
      }
      
      return document;
    } catch (error) {
      console.error(`Failed to get document ${id}:`, error);
      throw error;
    }
  }

  async getDocumentsByUserId(userId: string, limit = 50, offset = 0) {
    try {
      return await this.documentRepository.findByUserId(userId, limit, offset);
    } catch (error) {
      console.error(`Failed to get documents for user ${userId}:`, error);
      throw new Error(`Failed to get documents: ${error.message}`);
    }
  }

  async getDocumentsByStatus(status: string, limit = 50, offset = 0) {
    try {
      return await this.documentRepository.findByStatus(status, limit, offset);
    } catch (error) {
      console.error(`Failed to get documents with status ${status}:`, error);
      throw new Error(`Failed to get documents: ${error.message}`);
    }
  }

  async updateDocument(data: UpdateDocumentDto): Promise<void> {
    try {
      // Check if document exists
      const exists = await this.documentRepository.exists(data.id);
      if (!exists) {
        throw new Error(`Document with ID ${data.id} not found`);
      }
      
      const { id, ...updateData } = data;
      await this.documentRepository.update(id, updateData);
      
      console.log(`Document ${id} updated successfully`);
    } catch (error) {
      console.error(`Failed to update document ${data.id}:`, error);
      throw error;
    }
  }

  async updateStatus(data: UpdateDocumentStatusDto): Promise<void> {
    try {
      // Check if document exists
      const exists = await this.documentRepository.exists(data.id);
      if (!exists) {
        throw new Error(`Document with ID ${data.id} not found`);
      }
      
      await this.documentRepository.updateStatus(data.id, data.status, data.error_message);
      
      console.log(`Document status updated successfully for ID: ${data.id} to ${data.status}`);
    } catch (error) {
      console.error(`Failed to update document status for ${data.id}:`, error);
      throw error;
    }
  }

  async deleteDocument(id: string): Promise<void> {
    try {
      // Check if document exists
      const exists = await this.documentRepository.exists(id);
      if (!exists) {
        throw new Error(`Document with ID ${id} not found`);
      }
      
      // Note: We don't handle chunk deletion here - that's the responsibility of ChunkService
      // or a transaction in a higher-level service
      await this.documentRepository.delete(id);
      
      console.log(`Document ${id} deleted successfully`);
    } catch (error) {
      console.error(`Failed to delete document ${id}:`, error);
      throw error;
    }
  }

  async getDocumentStats(userId?: string) {
    try {
      return await this.documentRepository.getStats(userId);
    } catch (error) {
      console.error('Failed to get document stats:', error);
      throw new Error(`Failed to get document stats: ${error.message}`);
    }
  }
}