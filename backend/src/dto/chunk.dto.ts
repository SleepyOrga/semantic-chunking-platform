export interface AddChunkDto {
  document_id: string;
  chunk_index: number;
  content: string;
  embedding: number[];
}

export interface UpdateChunkDto {
  id: string;
  content?: string;
  embedding?: number[];
}

export interface ChunkQuery {
  document_id?: string;
  limit?: number;
  offset?: number;
}

export interface SimilaritySearchDto {
  embedding: number[];
  limit?: number;
  threshold?: number;
}