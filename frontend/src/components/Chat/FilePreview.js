// src/components/Chat/FilePreview.js
import React from 'react';
import { Box, Typography, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

const FilePreview = ({ file, onClear }) => {
  if (!file) return null;
  
  // Function to determine file type icon
  const getFileIcon = () => {
    const extension = file.name.split('.').pop().toLowerCase();
    
    switch(extension) {
      case 'pdf':
        return '📄';
      case 'docx':
      case 'doc':
        return '📝';
      case 'xlsx':
      case 'xls':
        return '📊';
      case 'jpg':
      case 'jpeg':
      case 'png':
        return '🖼️';
      case 'txt':
        return '📃';
      default:
        return '📁';
    }
  };
  
  return (
    <Box 
      sx={{ 
        position: 'absolute', 
        bottom: '100%', 
        left: 16,
        right: 16,
        py: 2,
        px: 3, 
        my: 1,
        mx: { xs: 0, sm: 2 },
        background: 'rgba(255,255,255,0.95)',
        backdropFilter: 'blur(8px)',
        borderRadius: '12px',
        border: '1px solid rgba(88, 167, 254, 0.2)',
        boxShadow: '0 8px 20px rgba(0,0,0,0.1)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        animation: 'slideInUp 0.3s ease-out',
        '@keyframes slideInUp': {
          '0%': { transform: 'translateY(20px)', opacity: 0 },
          '100%': { transform: 'translateY(0)', opacity: 1 }
        }
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        <Box 
          sx={{ 
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 40,
            height: 40,
            borderRadius: '50%',
            mr: 2,
            background: 'linear-gradient(45deg, rgba(127, 231, 134, 0.2), rgba(88, 167, 254, 0.2))',
            border: '1px solid rgba(88, 167, 254, 0.1)',
            fontSize: '20px',
          }}
        >
          {getFileIcon()}
        </Box>
        <Box>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#37474f' }} noWrap>
            {file.name}
          </Typography>
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
            {(file.size / 1024).toFixed(1)} KB • Ready to upload
          </Typography>
        </Box>
      </Box>
      <IconButton 
        onClick={onClear}
        sx={{
          background: 'rgba(0,0,0,0.05)',
          borderRadius: '8px',
          '&:hover': {
            background: 'rgba(0,0,0,0.1)',
          }
        }}
      >
        <CloseIcon fontSize="small" />
      </IconButton>
    </Box>
  );
};

export default FilePreview;