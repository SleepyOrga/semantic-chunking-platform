// src/components/common/LoadingIndicator.js
import React from 'react';
import { Box, CircularProgress } from '@mui/material';

const LoadingIndicator = () => {
  return (
    <Box 
      sx={{ 
        display: 'flex', 
        flexDirection: 'column',
        alignItems: 'center', 
        justifyContent: 'center', 
        my: 2,
        p: 3,
      }}
    >
      <Box
        sx={{
          position: 'relative',
          animation: 'pulse 1.5s infinite ease-in-out',
          '@keyframes pulse': {
            '0%': { opacity: 0.6, transform: 'scale(0.98)' },
            '50%': { opacity: 1, transform: 'scale(1.01)' },
            '100%': { opacity: 0.6, transform: 'scale(0.98)' }
          }
        }}
      >
        <CircularProgress 
          size={36} 
          sx={{ 
            color: '#58A7FE',
            opacity: 0.7,
          }} 
        />
        <CircularProgress 
          size={36} 
          sx={{ 
            color: '#7FE786',
            position: 'absolute',
            left: 0,
            animationDuration: '1s',
            opacity: 0.8
          }} 
        />
      </Box>
    </Box>
  );
};

export default LoadingIndicator;