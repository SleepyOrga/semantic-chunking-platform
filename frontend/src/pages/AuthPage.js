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
    <Container maxWidth="lg" sx={{ py: 6 }}>
      <Box sx={{ 
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        minHeight: '80vh',
        justifyContent: 'center'
      }}>
        <Box 
          sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            mb: 4,
            background: 'linear-gradient(45deg, #7FE786, #58A7FE)',
            p: 2,
            borderRadius: 2,
            boxShadow: '0 4px 20px rgba(88, 167, 254, 0.15)'
          }}
        >
          <AutoAwesomeIcon sx={{ fontSize: 40, color: '#fff', mr: 1 }} />
          <Typography variant="h4" component="h1" fontWeight="600" color="white">
            Sema
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
            Welcome to Sema
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