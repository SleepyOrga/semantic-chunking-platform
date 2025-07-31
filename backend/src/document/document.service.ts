import { Injectable, HttpException, HttpStatus, Inject, forwardRef } from '@nestjs/common';
import { DocumentRepository } from '../repositories/document.repository';
import { S3Service } from '../upload/s3.service';
import { ChunkService } from '../chunk/chunk.service';
import {
  CreateDocumentDto,
  UpdateDocumentDto,
  UpdateDocumentStatusDto,
  DocumentQuery,
} from '../dto/document.dto';

@Injectable()
export class DocumentService {
  constructor(
    private readonly documentRepository: DocumentRepository,
    @Inject(forwardRef(() => S3Service))
    private readonly s3Service: S3Service,
    private readonly chunkService: ChunkService,
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

  async getDocumentById(id: string, userId?: string) {
    try {
      const document = await this.documentRepository.findById(id);

      if (!document) {
        throw new HttpException(`Document with ID ${id} not found`, HttpStatus.NOT_FOUND);
      }

      // If userId is provided, verify ownership
      if (userId && document.user_id !== userId) {
        throw new HttpException('Access denied', HttpStatus.FORBIDDEN);
      }

      console.log('[DEBUG] Returning document details:', {
        id: document.id,
        filename: document.filename,
        path: document.path,
        status: document.status
      });

      return document;
    } catch (error) {
      console.error(`Failed to get document ${id}:`, error);
      if (error instanceof HttpException) {
        throw error;
      }
      throw new HttpException('Internal server error', HttpStatus.INTERNAL_SERVER_ERROR);
    }
  }

  async getDocumentsByUserId(userId: string, limit = 50, offset = 0) {
    try {
      const documents = await this.documentRepository.findByUserId(
        userId,
        limit,
        offset,
      );
      return {
        documents: documents.map((doc) => ({
          id: doc.id,
          filename: doc.filename,
          mimetype: doc.mimetype,
          size: doc.size,
          status: doc.status,
          uploadedAt: doc.created_at,
        })),
      };
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

      await this.documentRepository.updateStatus(
        data.id,
        data.status,
        data.error_message,
      );

      console.log(
        `Document status updated successfully for ID: ${data.id} to ${data.status}`,
      );
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

  async getRawFile(id: string, userId: string): Promise<{ stream: NodeJS.ReadableStream; filename: string; mimetype: string }> {
    try {
      const document = await this.getDocumentById(id, userId);
      
      if (!document.path) {
        throw new HttpException('Raw file not available', HttpStatus.NOT_FOUND);
      }

      const stream = await this.s3Service.getFileStream(document.path);
      
      return {
        stream,
        filename: document.filename,
        mimetype: document.mimetype,
      };
    } catch (error) {
      console.error(`Failed to get raw file for document ${id}:`, error);
      if (error instanceof HttpException) {
        throw error;
      }
      throw new HttpException('Failed to fetch raw file', HttpStatus.INTERNAL_SERVER_ERROR);
    }
  }

  async getParsedMarkdown(id: string, userId: string): Promise<{ content: string; filename: string }> {
    try {
      const document = await this.getDocumentById(id, userId);
      if (!document.path) {
        throw new HttpException('Parsed markdown not available', HttpStatus.NOT_FOUND);
      }

      // List objects in the parsed/{document.id}/ folder to find the .md file
      const prefix = `parsed/${document.id}/`;
      const files = await this.s3Service.listFiles(prefix);
      const mdFile = files.find((f: string) => f.endsWith('.md'));
      if (!mdFile) {
        throw new HttpException('Parsed markdown not found in S3', HttpStatus.NOT_FOUND);
      }
      const content = await this.s3Service.getFileContent(mdFile);
      return {
        content,
        filename: mdFile.split('/').pop() || `${document.filename}.md`,
      };
    } catch (error) {
      console.error(`Failed to get parsed markdown for document ${id}:`, error);
      if (error instanceof HttpException) {
        throw error;
      }
      throw new HttpException('Failed to fetch parsed markdown', HttpStatus.INTERNAL_SERVER_ERROR);
    }
  }

  async getDocumentChunks(id: string, userId: string): Promise<{ chunks: any[]; filename: string }> {
    try {
      const document = await this.getDocumentById(id, userId);
      
      const chunks = await this.chunkService.getChunksByDocumentId(id);
      
      return {
        chunks,
        filename: `${document.filename}_chunks.json`,
      };
    } catch (error) {
      console.error(`Failed to get chunks for document ${id}:`, error);
      if (error instanceof HttpException) {
        throw error;
      }
      throw new HttpException('Failed to fetch document chunks', HttpStatus.INTERNAL_SERVER_ERROR);
    }
  }
}
