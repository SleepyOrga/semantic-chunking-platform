// src/services/SearchService.js
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:4000';

class SearchService {
  async searchDocuments(query) {
    try {
      const response = await axios.post(`${API_URL}/search`, 
        { query },
        {
          headers: {
            'Authorization': `Bearer ${this.getAuthToken()}`
          }
        }
      );
      
      return response.data;
    } catch (error) {
      throw error.response?.data || { message: 'Search failed' };
    }
  }

  getAuthToken() {
    const user = JSON.parse(localStorage.getItem('user'));
    return user?.token;
  }
}

export default new SearchService();