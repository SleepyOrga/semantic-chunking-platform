// src/components/Header/Header.js
import React from 'react';
import { Box, Typography, IconButton, Badge, Button } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import LogoutIcon from '@mui/icons-material/Logout';
import authService from '../../services/AuthService';
import { useNavigate } from 'react-router-dom';

const Header = ({ sidebarOpen, toggleSidebar, documentCount }) => {
  const navigate = useNavigate();
  const isAuthenticated = authService.isAuthenticated();
  
  const handleLogout = () => {
    authService.logout();
    navigate('/auth');
  };

  return (
    <Box 
      sx={{ 
        p: 2, 
        borderBottom: '1px solid #e0e0e0', 
        bgcolor: 'white',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between' // This spreads out the content
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        {!sidebarOpen && (
          <IconButton 
            onClick={toggleSidebar} 
            sx={{ mr: 1 }}
            aria-label="Open documents sidebar"
          >
            <Badge 
              badgeContent={documentCount} 
              color="primary"
              invisible={documentCount === 0}
            >
              <MenuIcon />
            </Badge>
          </IconButton>
        )}
        <AutoAwesomeIcon sx={{ mr: 1, color: '#6e41e2' }} />
        <Typography variant="h6" component="div">
          Semantic Search Assistant
        </Typography>
      </Box>
      
      {/* Logout button section */}
      {isAuthenticated && (
        <Button
          variant="outlined"
          color="primary"
          size="small"
          startIcon={<LogoutIcon />}
          onClick={handleLogout}
          sx={{ ml: 2 }}
        >
          Logout
        </Button>
      )}
    </Box>
  );
};

export default Header;