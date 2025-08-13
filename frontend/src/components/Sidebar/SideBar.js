import React, { useEffect, useState } from 'react';
import { Box, Drawer, Typography, IconButton, Button, Tooltip } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import FolderIcon from '@mui/icons-material/Folder';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import FileList from './FileList';
import EmptyDocuments from './EmptyDocuments';

const SIDEBAR_WIDTH = 320;

const Sidebar = ({ 
  open, 
  onClose, 
  isMobile, 
  files, 
  onDeleteFile, 
  onUploadClick,
  onViewFile 
}) => {
  // Use state to handle animation safely
  const [render, setRender] = useState(false);
  
  // Safely handle animations after component mounts
  useEffect(() => {
    if (open) {
      const timer = setTimeout(() => {
        setRender(true);
      }, 100);
      return () => clearTimeout(timer);
    } else {
      setRender(false);
    }
  }, [open]);

  return (
    <Drawer
      variant={isMobile ? "temporary" : "persistent"}
      open={open}
      onClose={onClose}
      sx={{
        width: SIDEBAR_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: SIDEBAR_WIDTH,
          boxSizing: 'border-box',
          borderRight: 'none',
          boxShadow: '0px 3px 15px rgba(0,0,0,0.1)',
          backgroundColor: '#f8fafc',
          transition: 'all 0.3s ease-in-out',
        },
      }}
    >
      <Box sx={{ 
        p: 2.5, 
        display: 'flex', 
        alignItems: 'center',
        borderBottom: '1px solid rgba(0,0,0,0.06)',
        background: 'linear-gradient(135deg, #7FE786 0%, #58A7FE 100%)',
        color: 'white',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        opacity: render ? 1 : 0.8,
        transition: 'opacity 0.5s ease-in-out',
      }}>
        <FolderIcon sx={{ 
          mr: 1.5, 
          color: 'white',
          fontSize: '1.8rem',
          filter: 'drop-shadow(0px 1px 2px rgba(0,0,0,0.2))'
        }} />
        <Typography 
          variant="h6" 
          component="div" 
          sx={{ 
            flexGrow: 1, 
            color: 'white',
            fontWeight: 600,
            letterSpacing: '0.5px',
            textShadow: '0px 1px 2px rgba(0,0,0,0.1)'
          }}
        >
          My Documents
        </Typography>
        <Tooltip title="Close sidebar" arrow>
          <IconButton 
            onClick={onClose} 
            sx={{ 
              display: { sm: 'none' }, 
              color: 'white',
              '&:hover': {
                backgroundColor: 'rgba(255,255,255,0.15)',
                transform: 'scale(1.05)',
              },
              transition: 'all 0.2s ease'
            }}
          >
            <CloseIcon />
          </IconButton>
        </Tooltip>
      </Box>

      <Box sx={{ 
        overflowY: 'auto', 
        height: '100%',
        opacity: render ? 1 : 0.8,
        transition: 'opacity 0.6s ease-in-out',
        '&::-webkit-scrollbar': {
          width: '6px',
        },
        '&::-webkit-scrollbar-track': {
          background: 'rgba(0,0,0,0.02)',
        },
        '&::-webkit-scrollbar-thumb': {
          background: 'rgba(0,0,0,0.1)',
          borderRadius: '3px',
          '&:hover': {
            background: 'rgba(0,0,0,0.2)',
          }
        }
      }}>
        {files.length === 0 ? (
          <EmptyDocuments onUploadClick={onUploadClick} />
        ) : (
          <FileList files={files} onDeleteFile={onDeleteFile} onViewFile={onViewFile} />
        )}
      </Box>

      <Box sx={{ 
        p: 2.5, 
        borderTop: '1px solid rgba(0,0,0,0.06)',
        backgroundColor: 'rgba(255,255,255,0.5)',
        opacity: render ? 1 : 0.8,
        transition: 'opacity 0.7s ease-in-out',
      }}>
        <Button
          fullWidth
          variant="contained"
          startIcon={<AttachFileIcon />}
          onClick={onUploadClick}
          sx={{ 
            py: 1.2,
            background: 'linear-gradient(135deg, #7FE786 0%, #58A7FE 100%)',
            boxShadow: '0 2px 8px rgba(88,167,254,0.3)',
            borderRadius: '8px',
            fontWeight: 600,
            textTransform: 'none',
            fontSize: '0.95rem',
            transition: 'all 0.3s ease',
            '&:hover': { 
              background: 'linear-gradient(135deg, #6BD673 0%, #4592E6 100%)',
              boxShadow: '0 4px 12px rgba(88,167,254,0.4)',
              transform: 'translateY(-2px)'
            },
            '&:active': {
              transform: 'translateY(0px)',
              boxShadow: '0 1px 5px rgba(88,167,254,0.4)',
            }
          }}
        >
          Upload New Document
        </Button>
      </Box>
    </Drawer>
  );
};

export default Sidebar;