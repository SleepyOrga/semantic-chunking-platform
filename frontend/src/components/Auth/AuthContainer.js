// src/components/Auth/AuthContainer.js
import React, { useState } from 'react';
import { Paper, Tabs, Tab, Box } from '@mui/material';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';

const AuthContainer = ({ onLoginSuccess }) => {
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  return (
    <Paper 
      elevation={3} 
      sx={{ 
        maxWidth: 450, 
        width: '100%', 
        mx: 'auto', 
        mt: 4,
        overflow: 'hidden'
      }}
    >
      <Tabs 
        value={activeTab} 
        onChange={handleTabChange} 
        variant="fullWidth"
        sx={{ 
          borderBottom: '1px solid #e0e0e0',
          bgcolor: '#f5f5f5'
        }}
      >
        <Tab label="Login" />
        <Tab label="Sign Up" />
      </Tabs>
      
      <Box sx={{ p: 3 }}>
        {activeTab === 0 ? (
          <LoginForm onLoginSuccess={onLoginSuccess} />
        ) : (
          <RegisterForm onRegisterSuccess={() => setActiveTab(0)} />
        )}
      </Box>
    </Paper>
  );
};

export default AuthContainer;