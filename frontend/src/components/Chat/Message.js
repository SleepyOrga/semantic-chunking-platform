// src/components/Chat/Message.js
import React from 'react';
import { Box, Paper, Typography, Avatar } from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';

const Message = ({ message }) => {
  return (
    <Box 
      sx={{
        display: 'flex',
        mb: 2,
        maxWidth: '850px',
        alignSelf: message.type === 'user' ? 'flex-end' : 'flex-start'
      }}
    >
      {message.type === 'assistant' && (
        <Avatar sx={{ bgcolor: '#6e41e2', mr: 2 }}>
          <SmartToyIcon />
        </Avatar>
      )}
      
      <Paper 
        elevation={0}
        sx={{
          p: 2,
          borderRadius: 2,
          maxWidth: '90%',
          bgcolor: message.type === 'user' ? '#e6f3ff' : 'white',
          border: message.error ? '1px solid #f44336' : '1px solid #e0e0e0'
        }}
      >
        {message.isFile ? (
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <InsertDriveFileIcon sx={{ mr: 1 }} />
            <Typography>{message.content}</Typography>
          </Box>
        ) : (
          <Typography sx={{ whiteSpace: 'pre-wrap' }}>
            {message.content}
          </Typography>
        )}
      </Paper>
      
      {message.type === 'user' && (
        <Avatar sx={{ bgcolor: '#1976d2', ml: 2 }}>
          <PersonIcon />
        </Avatar>
      )}
    </Box>
  );
};

export default Message;