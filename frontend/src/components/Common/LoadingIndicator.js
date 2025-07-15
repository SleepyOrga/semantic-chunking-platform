// src/components/common/LoadingIndicator.js
import React from 'react';
import { Box, CircularProgress } from '@mui/material';

const LoadingIndicator = () => {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
      <CircularProgress size={30} sx={{ color: '#6e41e2' }} />
    </Box>
  );
};

export default LoadingIndicator;