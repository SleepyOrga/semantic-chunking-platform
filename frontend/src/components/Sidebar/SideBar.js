// src/components/Sidebar/Sidebar.js
import React from 'react';
import { Box, Drawer, Typography, IconButton, Button } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import FolderIcon from '@mui/icons-material/Folder';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import FileList from './FileList';
import EmptyDocuments from './EmptyDocuments';

const SIDEBAR_WIDTH = 280;

const Sidebar = ({ 
  open, 
  onClose, 
  isMobile, 
  files, 
  onDeleteFile, 
  onUploadClick 
}) => {
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
          borderRight: '1px solid #e0e0e0',
          backgroundColor: '#f8f9fa'
        },
      }}
    >
      <Box sx={{ 
        p: 2, 
        display: 'flex', 
        alignItems: 'center',
        borderBottom: '1px solid #e0e0e0',
        bgcolor: '#f0f2f5'
      }}>
        <FolderIcon sx={{ mr: 1, color: '#6e41e2' }} />
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          My Documents
        </Typography>
        <IconButton onClick={onClose} sx={{ display: { sm: 'none' } }}>
          <CloseIcon />
        </IconButton>
      </Box>

      {files.length === 0 ? (
        <EmptyDocuments onUploadClick={onUploadClick} />
      ) : (
        <>
          <FileList files={files} onDeleteFile={onDeleteFile} />
          <Box sx={{ p: 2, borderTop: '1px solid #e0e0e0' }}>
            <Button
              fullWidth
              variant="contained"
              startIcon={<AttachFileIcon />}
              onClick={onUploadClick}
              sx={{ 
                bgcolor: '#6e41e2',
                '&:hover': { bgcolor: '#5a32c5' }
              }}
            >
              Upload New Document
            </Button>
          </Box>
        </>
      )}
    </Drawer>
  );
};

export default Sidebar;