// src/components/Chat/WelcomeScreen.js - Fixed syntax error
import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import AttachFileIcon from '@mui/icons-material/AttachFile';

const WelcomeScreen = ({ onUploadClick }) => {
  return (
    <Box 
      sx={{ 
        textAlign: 'center', 
        maxWidth: '600px', 
        mx: 'auto', 
        my: 5,
        bgcolor: 'white',
        borderRadius: 4,
        boxShadow: '0 10px 40px rgba(0,0,0,0.1)',
        background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
        border: '1px solid rgba(0,0,0,0.05)',
        overflow: 'hidden',
        animation: 'fadeIn 1s ease-out',
        '@keyframes fadeIn': {
          '0%': { opacity: 0, transform: 'translateY(20px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' }
        }
      }}
    >
      <Box 
        sx={{ 
          background: 'linear-gradient(135deg, #7FE786 0%, #58A7FE 100%)',
          p: 5,
          position: 'relative',
          overflow: 'hidden',
          mb: 4
        }}
      >
        <Box 
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            opacity: 0.1,
            backgroundImage: 'url("data:image/svg+xml,%3Csvg width=\'100\' height=\'100\' viewBox=\'0 0 100 100\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cpath d=\'M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm-43-7c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm63 31c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM34 90c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm56-76c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM12 86c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm28-65c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm23-11c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-6 60c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm29 22c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zM32 63c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm57-13c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-9-21c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM60 91c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM35 41c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM12 60c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2z\' fill=\'%23ffffff\' fill-opacity=\'1\' fill-rule=\'evenodd\'/%3E%3C/svg%3E")',
          }}
        />
        <UploadFileIcon 
          sx={{ 
            fontSize: 80, 
            color: 'white', 
            mb: 3,
            filter: 'drop-shadow(0 3px 5px rgba(0,0,0,0.2))',
          }} 
        />
        <Typography 
          variant="h4" 
          gutterBottom 
          sx={{ 
            color: 'white',
            fontWeight: 700,
            letterSpacing: '0.5px',
            textShadow: '0 2px 4px rgba(0,0,0,0.15)',
          }}
        >
          Welcome to Sema
        </Typography>
        <Typography 
          variant="subtitle1" 
          sx={{
            color: 'rgba(255,255,255,0.9)',
            maxWidth: '80%',
            mx: 'auto',
          }}
        >
          Your AI-powered document assistant
        </Typography>
      </Box>
      
      <Box sx={{ px: 4, pb: 5 }}>
        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
          Upload Documents & Ask Questions
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph sx={{ mb: 4, maxWidth: '80%', mx: 'auto' }}>
          Upload your documents and ask questions about their content.
          I'll use semantic search to find the most relevant information.
        </Typography>
        <Button 
          variant="contained" 
          startIcon={<AttachFileIcon />}
          onClick={onUploadClick}
          sx={{ 
            py: 1.5,
            px: 4,
            borderRadius: 8,
            background: 'linear-gradient(45deg, #7FE786, #58A7FE)',
            boxShadow: '0 4px 15px rgba(0,0,0,0.1)',
            fontSize: '1rem',
            fontWeight: 600,
            textTransform: 'none',
            transition: 'all 0.3s ease',
            '&:hover': { 
              background: 'linear-gradient(45deg, #6BD673, #4592E6)',
              boxShadow: '0 6px 20px rgba(0,0,0,0.15)',
              transform: 'translateY(-2px)'
            },
            '&:active': {
              transform: 'translateY(0)',
              boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
            }
          }}
        >
          Upload a Document
        </Button>
      </Box>
    </Box>
  );
};

export default WelcomeScreen;