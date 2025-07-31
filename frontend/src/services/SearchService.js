import axios from 'axios';
import AuthService from './AuthService';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:4000';
const RETRIEVAL_API_URL = process.env.REACT_APP_RETRIEVAL_API_URL || 'http://localhost:8000';

class SearchService {
  async searchDocuments(query, options = {}) {
    try {
      const token = AuthService.getAuthToken();
      
      // Call the retrieval service RAG endpoint
      const response = await axios.post(`${RETRIEVAL_API_URL}/rag`, {
        query: query,
        top_k_chunks: options.topK || 20,
        final_n: options.finalN || 5,
        expand_query: options.expandQuery !== false,
        use_hybrid: options.useHybrid !== false,
        use_tag_filtering: options.useTagFiltering !== false
      }, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });
      
      const chunks = response.data;
      
      // Format the response for the UI
      return {
        result: this.formatSearchResults(chunks, query),
        rawChunks: chunks
      };
    } catch (error) {
      console.error('Error in search:', error);
      throw error.response?.data || { message: 'Search failed' };
    }
  }
  
  // Format the raw chunks into a readable response
  formatSearchResults(chunks, query) {
    if (!chunks || chunks.length === 0) {
      return `I couldn't find any relevant information for "${query}".`;
    }
    
    // Create a summary of found documents
    const uniqueDocIds = new Set(chunks.map(chunk => chunk.document_id));
    const documentCount = uniqueDocIds.size;
    
    let response = `I found ${chunks.length} relevant passages from ${documentCount} document${documentCount > 1 ? 's' : ''} for your query:\n\n`;
    
    // Add each chunk with formatting
    chunks.forEach((chunk, index) => {
      const confidenceText = chunk.score >= 0.8 ? "high confidence" : 
                           chunk.score >= 0.5 ? "medium confidence" : "low confidence";
      
      response += `**Passage ${index + 1}** (${confidenceText}):\n`;
      response += chunk.content + '\n\n';
    });
    
    return response;
  }
  
  // Optional: Add a health check method to test connectivity
  async checkRetrievalServiceHealth() {
    try {
      const response = await axios.get(`${RETRIEVAL_API_URL}/health`);
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }
}

export default new SearchService();