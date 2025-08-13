// src/chunk/chunk.controller.ts
import { Controller, Get, Post, Put, Delete, Body, Param, Query, UseGuards } from '@nestjs/common';
import { ChunkService } from './chunk.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import {
  AddChunkDto,
  UpdateChunkDto,
  SimilaritySearchDto,
  TagSearchDto,
  ChunkTagsDto
} from '../dto/chunk.dto';

@Controller('chunks')
export class ChunkController {
  constructor(private readonly chunkService: ChunkService) {}

  @Post()
  async addChunk(@Body() addChunkDto: AddChunkDto): Promise<{ id: string }> {
    const chunkId = await this.chunkService.addChunk(addChunkDto);
    return { id: chunkId };
  }

  @Get('document/:documentId')
  async getChunksByDocumentId(@Param('documentId') documentId: string) {
    const chunks = await this.chunkService.getChunksByDocumentId(documentId);
    return { chunks };
  }

  @Get(':id')
  async getChunkById(@Param('id') id: string) {
    const chunk = await this.chunkService.getChunkById(id);
    return { chunk };
  }

  @Put()
  async updateChunk(@Body() updateChunkDto: UpdateChunkDto) {
    await this.chunkService.updateChunk(updateChunkDto);
    return { message: 'Chunk updated successfully' };
  }

  @Delete(':id')
  async deleteChunk(@Param('id') id: string) {
    await this.chunkService.deleteChunk(id);
    return { message: 'Chunk deleted successfully' };
  }

  @Delete('document/:documentId')
  async deleteChunksByDocumentId(@Param('documentId') documentId: string) {
    await this.chunkService.deleteChunksByDocumentId(documentId);
    return { message: 'All chunks for document deleted successfully' };
  }

  @Post('search/similarity')
  @UseGuards(JwtAuthGuard)
  async searchSimilarChunks(@Body() searchDto: SimilaritySearchDto) {
    const results = await this.chunkService.searchSimilarChunks(searchDto);
    return { results };
  }

  // New tag endpoints

  @Get(':id/tags')
  async getChunkTags(@Param('id') id: string) {
    return this.chunkService.getChunkTags(id);
  }

  @Put(':id/tags')
  async setChunkTags(@Param('id') id: string, @Body() tagsDto: ChunkTagsDto) {
    return this.chunkService.setChunkTags(id, tagsDto);
  }

  @Post(':id/tags')
  async addChunkTags(@Param('id') id: string, @Body() tagsDto: ChunkTagsDto) {
    return this.chunkService.addTagsToChunk(id, tagsDto);
  }

  @Delete(':id/tags')
  async removeChunkTags(@Param('id') id: string, @Body() tagsDto: ChunkTagsDto) {
    return this.chunkService.removeTagsFromChunk(id, tagsDto);
  }

  @Post('search/tags')
  @UseGuards(JwtAuthGuard)
  async searchByTags(@Body() searchDto: TagSearchDto) {
    return this.chunkService.searchByTags(searchDto);
  }
}