// src/components/common/ErrorAlert.js
import React from 'react';
import { Alert } from '@mui/material';

const ErrorAlert = ({ error, onClose }) => {
  if (!error) return null;
  
  return (
    <Alert 
      severity="error" 
      onClose={onClose}
      sx={{ m: 2 }}
    >
      {error}
    </Alert>
  );
};

export default ErrorAlert;