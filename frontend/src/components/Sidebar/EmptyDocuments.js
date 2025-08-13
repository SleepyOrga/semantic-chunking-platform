// src/components/Sidebar/EmptyDocuments.js
import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import AttachFileIcon from '@mui/icons-material/AttachFile';

const EmptyDocuments = ({ onUploadClick }) => {
  return (
    <Box sx={{ 
      p: 4, 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center',
      justifyContent: 'center',
      height: '50%',
      animation: 'fadeIn 0.8s ease-in-out',
      '@keyframes fadeIn': {
        '0%': { opacity: 0, transform: 'translateY(10px)' },
        '100%': { opacity: 1, transform: 'translateY(0)' }
      }
    }}>
      <Box 
        sx={{ 
          p: 3,
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #f8fafc 0%, #edf2f7 100%)',
          boxShadow: '0 4px 20px rgba(0,0,0,0.05)',
          mb: 3
        }}
      >
        <UploadFileIcon 
          sx={{ 
            fontSize: 70, 
            color: 'primary.main', 
            filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))'
          }} 
        />
      </Box>
      <Typography 
        variant="h6" 
        align="center"
        sx={{ 
          mb: 1.5,
          fontWeight: 600,
          background: 'linear-gradient(45deg, #1a202c, #4a5568)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}
      >
        Your Document Library is Empty
      </Typography>
      <Typography 
        variant="body2" 
        color="text.secondary" 
        align="center"
        sx={{ mb: 3, maxWidth: 220 }}
      >
        Upload your first document to get started with semantic search
      </Typography>
      <Button
        variant="contained"
        startIcon={<AttachFileIcon />}
        onClick={onUploadClick}
        sx={{ 
          mt: 1, 
          boxShadow: '0 4px 10px rgba(0,0,0,0.1)',
          background: 'linear-gradient(45deg, #7FE786, #58A7FE)',
          px: 3,
          py: 1.2,
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 500,
          fontSize: '0.95rem',
          transition: 'all 0.3s ease',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: '0 6px 15px rgba(0,0,0,0.15)'
          }
        }}
      >
        Upload Document
      </Button>
    </Box>
  );
};

export default EmptyDocuments;