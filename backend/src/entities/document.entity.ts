export interface DocumentEntity {
  id: string;
  user_id: string;
  filename: string;
  mimetype: string;
  size: number;
  path: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message?: string;
  created_at: Date;
}

export type CreateDocumentData = Omit<DocumentEntity, 'id' | 'created_at'>;
export type UpdateDocumentData = Partial<Omit<DocumentEntity, 'id' | 'created_at'>>;