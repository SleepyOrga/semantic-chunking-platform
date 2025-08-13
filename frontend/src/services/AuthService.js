import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:4000';

class AuthService {
  async login(email, password) {
    try {
      const response = await axios.post(`${API_URL}/auth/login`, {
        email,
        password
      });
      
      if (response.data.token) {
        localStorage.setItem('user', JSON.stringify(response.data));
        
        // Dispatch an event to notify the app that auth state has changed
        window.dispatchEvent(new Event('auth-change'));
      }
      
      return response.data;
    } catch (error) {
      throw error.response?.data || { message: 'Login failed' };
    }
  }

  async register(email, password, full_name) {
    try {
      const response = await axios.post(`${API_URL}/auth/register`, {
        email,
        password,
        full_name
      });
      
      if (response.data.token) {
        localStorage.setItem('user', JSON.stringify(response.data));
        
        // Dispatch an event to notify the app that auth state has changed
        window.dispatchEvent(new Event('auth-change'));
      }
      
      return response.data;
    } catch (error) {
      throw error.response?.data || { message: 'Registration failed' };
    }
  }

  logout() {
    localStorage.removeItem('user');
    // Dispatch the event on logout too
    window.dispatchEvent(new Event('auth-change'));
  }

  getCurrentUser() {
    try {
      return JSON.parse(localStorage.getItem('user'));
    } catch (e) {
      return null;
    }
  }

  isAuthenticated() {
    const user = this.getCurrentUser();
    const isAuth = !!user && !!user.token;
    console.log("Auth check:", isAuth);
    return isAuth;
  }
}

const authService = new AuthService();
export default authService;