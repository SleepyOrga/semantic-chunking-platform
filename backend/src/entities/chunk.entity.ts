export interface ChunkEntity {
  id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  embedding: number[];
  tag_embedding?: number[]; 
  created_at: Date;
}

export type CreateChunkData = Omit<ChunkEntity, 'id' | 'created_at'>;
export type UpdateChunkData = Partial<Omit<ChunkEntity, 'id' | 'created_at'>>;
