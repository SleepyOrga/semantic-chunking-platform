// src/components/Chat/FilePreview.js
import React from 'react';
import { Box, Typography, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';

const FilePreview = ({ file, onClear }) => {
  if (!file) return null;
  
  return (
    <Box 
      sx={{ 
        position: 'absolute', 
        bottom: '100%', 
        left: 0, 
        right: 0, 
        p: 1.5, 
        bgcolor: 'white',
        borderTop: '1px solid #e0e0e0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        <InsertDriveFileIcon sx={{ mr: 1 }} />
        <Typography variant="body2" noWrap>
          {file.name} ({(file.size / 1024).toFixed(1)} KB)
        </Typography>
      </Box>
      <IconButton size="small" onClick={onClear}>
        <CloseIcon fontSize="small" />
      </IconButton>
    </Box>
  );
};

export default FilePreview;