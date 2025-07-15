// src/components/Header/Header.js
import React from 'react';
import { Box, Typography, IconButton, Badge } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';

const Header = ({ sidebarOpen, toggleSidebar, documentCount }) => {
  return (
    <Box 
      sx={{ 
        p: 2, 
        borderBottom: '1px solid #e0e0e0', 
        bgcolor: 'white',
        display: 'flex',
        alignItems: 'center'
      }}
    >
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
  );
};

export default Header;