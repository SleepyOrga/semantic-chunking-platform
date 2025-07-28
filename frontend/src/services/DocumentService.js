// src/services/DocumentService.js
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:4000';

class DocumentService {
  async uploadDocument(file, userId) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('user_id', userId);
      
      const response = await axios.post(`${API_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${this.getAuthToken()}`
        }
      });
      
      return response.data;
    } catch (error) {
      throw error.response?.data || { message: 'Upload failed' };
    }
  }

  async getUserDocuments() {
    try {
      const response = await axios.get(`${API_URL}/documents`, {
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`
        }
      });
      
      return response.data;
    } catch (error) {
      throw error.response?.data || { message: 'Failed to fetch documents' };
    }
  }

  async deleteDocument(documentId) {
    try {
      await axios.delete(`${API_URL}/documents/${documentId}`, {
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`
        }
      });
      
      return { success: true };
    } catch (error) {
      throw error.response?.data || { message: 'Delete failed' };
    }
  }

  async getDocumentDetails(documentId) {
    try {
      const response = await axios.get(`${API_URL}/documents/${documentId}`, {
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`
        }
      });
      
      return response.data;
    } catch (error) {
      throw error.response?.data || { message: 'Failed to fetch document details' };
    }
  }

  async getRawFile(documentId) {
    try {
      const response = await axios.get(`${API_URL}/documents/${documentId}/raw`, {
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`
        },
        responseType: 'blob'
      });
      
      return response;
    } catch (error) {
      throw error.response?.data || { message: 'Failed to fetch raw file' };
    }
  }

  async getParsedMarkdown(documentId) {
    try {
      const response = await axios.get(`${API_URL}/documents/${documentId}/markdown`, {
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`
        }
      });
      
      return response.data;
    } catch (error) {
      throw error.response?.data || { message: 'Failed to fetch parsed markdown' };
    }
  }

  async getDocumentChunks(documentId) {
    try {
      const response = await axios.get(`${API_URL}/documents/${documentId}/chunks`, {
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`
        }
      });
      
      return response.data;
    } catch (error) {
      throw error.response?.data || { message: 'Failed to fetch document chunks' };
    }
  }

  getAuthToken() {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    return user.token || '';
  }
}

const documentService = new DocumentService();
export default documentService;