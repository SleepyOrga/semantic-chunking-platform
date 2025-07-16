import { Injectable, NotFoundException } from '@nestjs/common';
import { ChunkComponentRepository } from '../repositories/chunk-component.repository';
import { 
  CreateChunkComponentDto, 
  UpdateChunkComponentDto,
  SimilaritySearchDto 
} from '../dto/chunk-component.dto';

@Injectable()
export class ChunkComponentService {
  constructor(private readonly repository: ChunkComponentRepository) {}

  async findByChunkId(chunkId: string) {
    const components = await this.repository.findByChunkId(chunkId);
    return { components };
  }

  async findOne(id: string) {
    const component = await this.repository.findOne(id);
    if (!component) {
      throw new NotFoundException(`Chunk component with ID ${id} not found`);
    }
    return { component };
  }

  async create(createDto: CreateChunkComponentDto) {
    const id = await this.repository.create(createDto);
    const component = await this.repository.findOne(id);
    return { component, message: 'Chunk component created successfully' };
  }

  async createBulk(createDtos: CreateChunkComponentDto[]) {
    const ids = await this.repository.createBulk(createDtos);
    return { 
      count: ids.length, 
      ids, 
      message: `${ids.length} chunk components created successfully` 
    };
  }

  async update(id: string, updateDto: UpdateChunkComponentDto) {
    const component = await this.repository.findOne(id);
    if (!component) {
      throw new NotFoundException(`Chunk component with ID ${id} not found`);
    }

    await this.repository.update(id, updateDto);
    const updatedComponent = await this.repository.findOne(id);
    return { component: updatedComponent, message: 'Chunk component updated successfully' };
  }

  async remove(id: string) {
    const component = await this.repository.findOne(id);
    if (!component) {
      throw new NotFoundException(`Chunk component with ID ${id} not found`);
    }

    await this.repository.remove(id);
    return { message: 'Chunk component deleted successfully' };
  }

  async removeByChunkId(chunkId: string) {
    const count = await this.repository.removeByChunkId(chunkId);
    return { count, message: `${count} chunk components deleted successfully` };
  }

  async searchSimilar(searchDto: SimilaritySearchDto) {
    const results = await this.repository.searchSimilar(
      searchDto.embedding,
      searchDto.limit || 5,
      searchDto.threshold || 0.7
    );
    
    return { results };
  }
}