import { Controller, Get, Post, Put, Delete, Body, Param, Query, UseGuards } from '@nestjs/common';
import { ChunkComponentService } from './chunk-component.service';
import { 
  CreateChunkComponentDto, 
  UpdateChunkComponentDto,
  SimilaritySearchDto 
} from '../dto/chunk-component.dto';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';

@Controller('chunk-components')
export class ChunkComponentController {
  constructor(private readonly chunkComponentService: ChunkComponentService) {}

  @Get('chunk/:chunkId')
  async findByChunkId(@Param('chunkId') chunkId: string) {
    return this.chunkComponentService.findByChunkId(chunkId);
  }

  @Get(':id')
  async findOne(@Param('id') id: string) {
    return this.chunkComponentService.findOne(id);
  }

  @Post()
  async create(@Body() createDto: CreateChunkComponentDto) {
    return this.chunkComponentService.create(createDto);
  }

  @Put(':id')
  async update(@Param('id') id: string, @Body() updateDto: UpdateChunkComponentDto) {
    return this.chunkComponentService.update(id, updateDto);
  }

  @Delete(':id')
  async remove(@Param('id') id: string) {
    return this.chunkComponentService.remove(id);
  }

  @Post('search/similarity')
  @UseGuards(JwtAuthGuard)
  async searchSimilar(@Body() searchDto: SimilaritySearchDto) {
    return this.chunkComponentService.searchSimilar(searchDto);
  }

  @Post('bulk')
  async createBulk(@Body() createDtos: CreateChunkComponentDto[]) {
    return this.chunkComponentService.createBulk(createDtos);
  }

  @Delete('chunk/:chunkId')
  async removeByChunkId(@Param('chunkId') chunkId: string) {
    return this.chunkComponentService.removeByChunkId(chunkId);
  }
}