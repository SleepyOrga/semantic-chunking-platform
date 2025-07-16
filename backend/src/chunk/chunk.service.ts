// src/chunk/chunk.service.ts
import { Injectable, NotFoundException } from '@nestjs/common';
import { ChunkRepository } from '../repositories/chunk.repository';
import { 
  AddChunkDto, 
  UpdateChunkDto, 
  SimilaritySearchDto,
  TagSearchDto,
  ChunkTagsDto
} from '../dto/chunk.dto';

@Injectable()
export class ChunkService {
  constructor(private readonly chunkRepository: ChunkRepository) {}

  async getChunkById(id: string) {
    const chunk = await this.chunkRepository.findOne(id);
    if (!chunk) {
      throw new NotFoundException(`Chunk with ID ${id} not found`);
    }
    return chunk;
  }

  async getChunksByDocumentId(documentId: string) {
    return this.chunkRepository.findByDocumentId(documentId);
  }

  async addChunk(data: AddChunkDto): Promise<string> {
    return this.chunkRepository.create(data);
  }

  async updateChunk(data: UpdateChunkDto): Promise<void> {
    try {
      const chunk = await this.chunkRepository.findOne(data.id);
      if (!chunk) {
        throw new NotFoundException(`Chunk with ID ${data.id} not found`);
      }
      await this.chunkRepository.update(data);
    } catch (error) {
      console.error(`Failed to update chunk ${data.id}:`, error);
      throw error;
    }
  }

  async deleteChunk(id: string): Promise<void> {
    const chunk = await this.chunkRepository.findOne(id);
    if (!chunk) {
      throw new NotFoundException(`Chunk with ID ${id} not found`);
    }
    await this.chunkRepository.delete(id);
  }

  async deleteChunksByDocumentId(documentId: string): Promise<number> {
    return this.chunkRepository.deleteByDocumentId(documentId);
  }

  async searchSimilarChunks(searchDto: SimilaritySearchDto) {
    return this.chunkRepository.searchSimilar(
      searchDto.embedding,
      searchDto.limit || 5,
      searchDto.threshold || 0.7
    );
  }

  // New tag-related methods

  // Get tags for a chunk
  async getChunkTags(id: string) {
    const chunk = await this.chunkRepository.findOne(id);
    if (!chunk) {
      throw new NotFoundException(`Chunk with ID ${id} not found`);
    }
    return { tags: chunk.tags || [] };
  }

  // Add tags to a chunk
  async addTagsToChunk(id: string, tagsDto: ChunkTagsDto) {
    // Get existing tags
    const existingTags = await this.chunkRepository.getChunkTags(id);
    
    // Combine with new tags and remove duplicates
    const uniqueTags = [...new Set([...existingTags, ...tagsDto.tags])];
    
    // Update the chunk with the combined tags
    await this.chunkRepository.updateTags(id, uniqueTags);
    
    return { 
      message: 'Tags added successfully',
      tags: uniqueTags
    };
  }

  // Remove tags from a chunk
  async removeTagsFromChunk(id: string, tagsDto: ChunkTagsDto) {
    // Get existing tags
    const existingTags = await this.chunkRepository.getChunkTags(id);
    
    // Filter out the tags to remove
    const updatedTags = existingTags.filter(tag => !tagsDto.tags.includes(tag));
    
    // Update the chunk with the filtered tags
    await this.chunkRepository.updateTags(id, updatedTags);
    
    return { 
      message: 'Tags removed successfully',
      tags: updatedTags
    };
  }

  // Set all tags for a chunk (replace existing)
  async setChunkTags(id: string, tagsDto: ChunkTagsDto) {
    const chunk = await this.chunkRepository.findOne(id);
    if (!chunk) {
      throw new NotFoundException(`Chunk with ID ${id} not found`);
    }
    
    await this.chunkRepository.updateTags(id, tagsDto.tags);
    
    return { 
      message: 'Tags updated successfully',
      tags: tagsDto.tags
    };
  }

  // Search chunks by tags
  async searchByTags(searchDto: TagSearchDto) {
    let chunks;
    
    if (searchDto.matchAll) {
      // Find chunks that have ALL the specified tags
      chunks = await this.chunkRepository.findByAllTags(searchDto.tags, searchDto.limit || 10);
    } else {
      // Find chunks that have ANY of the specified tags
      chunks = await this.chunkRepository.findByTags(searchDto.tags, searchDto.limit || 10);
    }
    
    return { chunks };
  }
}