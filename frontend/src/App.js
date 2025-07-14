import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import HomePage from './pages/HomePage';
import AboutPage from './pages/AboutPage';
import AuthPage from './pages/AuthPage';
import AuthService from './services/AuthService';

function App() {
  // Use a function to get the current auth state rather than a static value
  const [isAuthenticated, setIsAuthenticated] = useState(() => AuthService.isAuthenticated());

  // Create a custom event to trigger auth state updates
  useEffect(() => {
    const updateAuthStatus = () => {
      const authStatus = AuthService.isAuthenticated();
      console.log("Auth status updated:", authStatus);
      setIsAuthenticated(authStatus);
    };

    // Update on mount
    updateAuthStatus();
    
    // Listen for auth changes via a custom event
    window.addEventListener('auth-change', updateAuthStatus);
    
    // Also listen for storage events (in case of multiple tabs)
    window.addEventListener('storage', (e) => {
      if (e.key === 'user') {
        updateAuthStatus();
      }
    });
    
    return () => {
      window.removeEventListener('auth-change', updateAuthStatus);
      window.removeEventListener('storage', updateAuthStatus);
    };
  }, []);
  
  console.log("Current auth state:", isAuthenticated);

  return (
    <Router>
      <Routes>
        <Route path="/auth" element={
          isAuthenticated ? <Navigate to="/" replace /> : <AuthPage />
        } />
        <Route path="/about" element={<AboutPage />} />
        <Route 
          path="/" 
          element={
            isAuthenticated ? (
              <HomePage />
            ) : (
              <Navigate to="/auth" replace />
            )
          } 
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;