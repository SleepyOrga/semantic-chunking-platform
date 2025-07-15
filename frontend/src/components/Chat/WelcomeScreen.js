// src/components/Chat/WelcomeScreen.js
import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import AttachFileIcon from '@mui/icons-material/AttachFile';

const WelcomeScreen = ({ onUploadClick }) => {
  return (
    <Box sx={{ 
      textAlign: 'center', 
      maxWidth: '600px', 
      mx: 'auto', 
      my: 4,
      p: 3,
      bgcolor: 'white',
      borderRadius: 2,
      boxShadow: 1
    }}>
      <UploadFileIcon sx={{ fontSize: 60, color: '#6e41e2', mb: 2 }} />
      <Typography variant="h5" gutterBottom>
        Upload Documents & Ask Questions
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Upload your documents and ask questions about their content.
        I'll use semantic search to find the most relevant information.
      </Typography>
      <Button 
        variant="contained" 
        startIcon={<AttachFileIcon />}
        onClick={onUploadClick}
        sx={{ 
          bgcolor: '#6e41e2', 
          '&:hover': { bgcolor: '#5a32c5' } 
        }}
      >
        Upload a Document
      </Button>
    </Box>
  );
};

export default WelcomeScreen;