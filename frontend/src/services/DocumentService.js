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

  getAuthToken() {
    const user = JSON.parse(localStorage.getItem('user'));
    return user?.token;
  }
}

export default new DocumentService();