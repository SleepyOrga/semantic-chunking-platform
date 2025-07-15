import { ChunkService } from '../chunk.service';
import { AddChunkDto } from '../../dto/chunk.dto';

export interface JobContext {
  services: {
    chunkService: ChunkService;
  };
}

export async function handle(
  payload: AddChunkDto,
  ctx: JobContext,
): Promise<{ chunk_id: string }> {
  try {
    console.log('Processing add chunk job:', payload);
    
    const chunkId = await ctx.services.chunkService.addChunk(payload);
    
    console.log(`Chunk added successfully with ID: ${chunkId}`);
    
    return { chunk_id: chunkId };
  } catch (error) {
    console.error('Failed to add chunk:', error);
    throw error;
  }
}