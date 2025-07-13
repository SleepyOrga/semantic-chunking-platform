// src/components/Sidebar/EmptyDocuments.js
import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import AttachFileIcon from '@mui/icons-material/AttachFile';

const EmptyDocuments = ({ onUploadClick }) => {
  return (
    <Box sx={{ 
      p: 3, 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center',
      justifyContent: 'center',
      height: '50%'
    }}>
      <UploadFileIcon sx={{ fontSize: 60, color: '#c7c7c7', mb: 2 }} />
      <Typography variant="body2" color="text.secondary" align="center">
        No documents uploaded yet
      </Typography>
      <Button
        variant="outlined"
        startIcon={<AttachFileIcon />}
        onClick={onUploadClick}
        sx={{ mt: 2 }}
      >
        Upload Document
      </Button>
    </Box>
  );
};

export default EmptyDocuments;