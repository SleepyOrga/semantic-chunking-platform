export interface CreateDocumentDto {
  user_id: string;
  filename: string;
  mimetype: string;
  size: number;
  path: string;
}

export interface UpdateDocumentDto {
  id: string;
  filename?: string;
  mimetype?: string;
  size?: number;
  path?: string;
  status?: 'pending' | 'processing' | 'completed' | 'failed';
  error_message?: string;
}

export interface UpdateDocumentStatusDto {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message?: string;
}

export interface DocumentQuery {
  user_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
}