// src/components/Auth/AuthContainer.js
import React, { useState } from 'react';
import { Paper, Tabs, Tab, Box } from '@mui/material';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';
import LoginIcon from '@mui/icons-material/Login';
import PersonAddIcon from '@mui/icons-material/PersonAdd';

const AuthContainer = ({ onLoginSuccess }) => {
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  return (
    <Paper 
      elevation={0} 
      sx={{ 
        maxWidth: 450, 
        width: '100%', 
        mx: 'auto',
        overflow: 'hidden',
        borderRadius: 3,
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.12)',
        border: '1px solid rgba(255,255,255,0.15)',
        background: 'rgba(255, 255, 255, 0.98)',
        backdropFilter: 'blur(15px)',
        position: 'relative',
        transition: 'opacity 0.6s ease, transform 0.6s ease',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '100%',
          background: 'linear-gradient(180deg, rgba(255,255,255,0.95) 0%, rgba(255,255,255,0.98) 100%)',
          zIndex: -1,
        },
        '&::after': {
          content: '""',
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: 6,
          background: 'linear-gradient(90deg, #58A7FE, #7FE786)',
          opacity: 0.7,
          zIndex: 0,
        }
      }}
    >
      <Tabs 
        value={activeTab} 
        onChange={handleTabChange} 
        variant="fullWidth"
        sx={{ 
          borderBottom: '1px solid rgba(0,0,0,0.06)',
          position: 'relative',
          '&::before': {
            content: '""',
            position: 'absolute',
            bottom: 0,
            left: 0,
            width: '100%',
            height: '1px',
            background: 'linear-gradient(90deg, rgba(88, 167, 254, 0.2), rgba(127, 231, 134, 0.2))',
            zIndex: 1,
          },
          '& .MuiTabs-indicator': {
            backgroundColor: activeTab === 0 ? '#58A7FE' : '#7FE786',
            height: 3,
            borderRadius: '3px 3px 0 0',
            transition: 'all 0.3s ease'
          },
          '& .MuiTab-root': {
            fontWeight: 600,
            fontSize: '1.05rem',
            textTransform: 'none',
            transition: 'all 0.3s ease',
            color: 'rgba(0, 0, 0, 0.5)',
            py: 2.2,
            '&.Mui-selected': {
              color: activeTab === 0 ? '#58A7FE' : '#7FE786'
            }
          }
        }}
      >
        <Tab 
          label="Login" 
          icon={<LoginIcon />} 
          iconPosition="start" 
          sx={{
            minHeight: 64,
            '& .MuiTab-iconWrapper': {
              mr: 1,
              transition: 'all 0.3s ease',
              opacity: activeTab === 0 ? 1 : 0.6,
            }
          }}
        />
        <Tab 
          label="Sign Up" 
          icon={<PersonAddIcon />} 
          iconPosition="start" 
          sx={{
            minHeight: 64,
            '& .MuiTab-iconWrapper': {
              mr: 1,
              transition: 'all 0.3s ease',
              opacity: activeTab === 1 ? 1 : 0.6,
            }
          }}
        />
      </Tabs>
      
      <Box 
        sx={{ 
          p: { xs: 2.5, sm: 3 },
          position: 'relative',
          zIndex: 1,
          transition: 'all 0.3s ease',
          animation: activeTab === 0 ? 'fadeIn 0.5s ease-out' : 'slideIn 0.5s ease-out',
          '@keyframes fadeIn': {
            '0%': { opacity: 0, transform: 'translateY(10px)' },
            '100%': { opacity: 1, transform: 'translateY(0)' }
          },
          '@keyframes slideIn': {
            '0%': { opacity: 0, transform: 'translateX(10px)' },
            '100%': { opacity: 1, transform: 'translateX(0)' }
          },
          '&::after': {
            content: '""',
            position: 'absolute',
            bottom: '5%',
            right: activeTab === 0 ? '10%' : '85%',
            width: 80,
            height: 80,
            background: activeTab === 0 
              ? 'radial-gradient(circle, rgba(88, 167, 254, 0.05) 0%, rgba(88, 167, 254, 0) 70%)'
              : 'radial-gradient(circle, rgba(127, 231, 134, 0.05) 0%, rgba(127, 231, 134, 0) 70%)',
            borderRadius: '50%',
            zIndex: -1,
            transition: 'right 0.5s ease-in-out',
          }
        }}
      >
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