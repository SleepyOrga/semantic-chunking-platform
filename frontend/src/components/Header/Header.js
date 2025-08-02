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
        px: 3,
        py: 1.5, 
        borderBottom: '1px solid rgba(0,0,0,0.06)', 
        background: 'rgba(255, 255, 255, 0.9)',
        backdropFilter: 'blur(10px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: '0 2px 10px rgba(0,0,0,0.03)',
        position: 'relative',
        zIndex: 5,
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        {!sidebarOpen && (
          <IconButton 
            onClick={toggleSidebar} 
            sx={{ 
              mr: 1.5, 
              color: 'grey.700',
              background: 'rgba(0,0,0,0.03)',
              borderRadius: '10px',
              '&:hover': {
                background: 'rgba(0,0,0,0.06)',
              }
            }}
            aria-label="Open documents sidebar"
          >
            <Badge 
              badgeContent={documentCount} 
              color="primary"
              invisible={documentCount === 0}
              sx={{
                '& .MuiBadge-badge': {
                  background: 'linear-gradient(45deg, #7FE786, #58A7FE)',
                  boxShadow: '0 2px 6px rgba(88, 167, 254, 0.3)',
                }
              }}
            >
              <MenuIcon />
            </Badge>
          </IconButton>
        )}
        
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          background: 'linear-gradient(45deg, #7FE786, #58A7FE)',
          borderRadius: '50%',
          width: 36,
          height: 36,
          justifyContent: 'center',
          boxShadow: '0 4px 10px rgba(88, 167, 254, 0.3)',
          mr: 2,
        }}>
          <AutoAwesomeIcon sx={{ color: 'white' }} />
        </Box>
        
        <Typography 
          variant="h6" 
          component="div"
          sx={{ 
            fontWeight: 700,
            backgroundImage: 'linear-gradient(45deg, #1a237e, #0d47a1)',
            backgroundClip: 'text',
            textFillColor: 'transparent',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            letterSpacing: '0.5px',
          }}
        >
          Sema
        </Typography>
        
        <Typography
          variant="subtitle2"
          sx={{
            ml: 1,
            color: 'text.secondary',
            fontWeight: 500,
            background: 'linear-gradient(45deg, #7FE786, #58A7FE)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          Assistant
        </Typography>
      </Box>
      
      {/* Logout button section */}
      {isAuthenticated && (
        <Button
          variant="contained"
          size="small"
          startIcon={<LogoutIcon />}
          onClick={handleLogout}
          sx={{ 
            ml: 2,
            background: 'linear-gradient(45deg, rgba(127, 231, 134, 0.1), rgba(88, 167, 254, 0.1))',
            color: '#37474f',
            boxShadow: 'none',
            borderRadius: '8px',
            textTransform: 'none',
            fontWeight: 500,
            px: 2,
            border: '1px solid rgba(88, 167, 254, 0.2)',
            '&:hover': {
              background: 'linear-gradient(45deg, rgba(127, 231, 134, 0.2), rgba(88, 167, 254, 0.2))',
              boxShadow: '0 2px 8px rgba(88, 167, 254, 0.15)',
            }
          }}
        >
          Logout
        </Button>
      )}
    </Box>
  );
};

export default Header;