// src/pages/AuthPage.js
import React from 'react';
import { Box, Container, Typography, Paper } from '@mui/material';
import AuthContainer from '../components/Auth/AuthContainer';
import { useNavigate } from 'react-router-dom';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';

const AuthPage = () => {
  const navigate = useNavigate();

  const handleLoginSuccess = (userData) => {
    console.log("User logged in:", userData);
    navigate('/');
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ 
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center'
      }}>
        <Box 
          sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            mb: 4
          }}
        >
          <AutoAwesomeIcon sx={{ fontSize: 40, color: '#6e41e2', mr: 1 }} />
          <Typography variant="h4" component="h1" fontWeight="500">
            Semantic Search Platform
          </Typography>
        </Box>

        <Paper
          elevation={0}
          sx={{
            p: 4,
            mb: 4,
            maxWidth: 800,
            bgcolor: '#f8f9fa',
            borderRadius: 2
          }}
        >
          <Typography variant="h5" gutterBottom>
            Welcome to Semantic Search Platform
          </Typography>
          <Typography variant="body1" paragraph>
            Upload your documents and use AI-powered semantic search to find exactly what you're looking for.
            Our platform helps you organize, search, and extract information from your documents with ease.
          </Typography>
          <Typography variant="body1">
            Please log in or create an account to get started.
          </Typography>
        </Paper>

        <AuthContainer onLoginSuccess={handleLoginSuccess} />
      </Box>
    </Container>
  );
};

export default AuthPage;