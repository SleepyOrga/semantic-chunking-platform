import { DocumentService } from '../document.service';
import { CreateDocumentDto } from '../../dto/document.dto';

export interface JobContext {
  services: {
    documentService: DocumentService;
  };
}

export async function handle(
  payload: CreateDocumentDto,
  ctx: JobContext,
): Promise<{ document_id: string }> {
  try {
    console.log('Processing create document job:', payload);
    
    const documentId = await ctx.services.documentService.createDocument(payload);
    
    console.log(`Document created successfully with ID: ${documentId}`);
    
    return { document_id: documentId };
  } catch (error) {
    console.error('Failed to create document:', error);
    throw error;
  }
}