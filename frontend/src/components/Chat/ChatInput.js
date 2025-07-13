// src/components/Chat/ChatInput.js
import React from 'react';
import { Paper, TextField, Button, IconButton } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import FilePreview from './FilePreview';

const ChatInput = ({ 
  input, 
  onInputChange, 
  onSubmit, 
  file, 
  onFileButtonClick, 
  onClearFile, 
  isLoading, 
  fileInputRef 
}) => {
  return (
    <Paper 
      component="form" 
      onSubmit={onSubmit}
      sx={{ 
        p: 2, 
        display: 'flex', 
        alignItems: 'center', 
        boxShadow: '0px -2px 10px rgba(0,0,0,0.05)',
        position: 'relative',
        bgcolor: 'white'
      }}
    >
      {/* File preview */}
      <FilePreview file={file} onClear={onClearFile} />

      {/* File upload button */}
      <IconButton 
        color="primary" 
        onClick={onFileButtonClick}
        disabled={isLoading}
      >
        <AttachFileIcon />
      </IconButton>

      {/* Message input */}
      <TextField
        fullWidth
        variant="outlined"
        placeholder={file 
          ? "Press send to upload your file..." 
          : "Ask a question about your documents..."
        }
        value={input}
        onChange={onInputChange}
        disabled={isLoading || !!file}
        sx={{ 
          mx: 1,
          '& .MuiOutlinedInput-root': {
            borderRadius: '24px',
          }
        }}
      />

      {/* Send button */}
      <Button
        variant="contained"
        endIcon={<SendIcon />}
        disabled={isLoading || (!input.trim() && !file)}
        type="submit"
        sx={{ 
          borderRadius: '24px',
          bgcolor: '#6e41e2',
          '&:hover': {
            bgcolor: '#5a32c5'
          }
        }}
      >
        {file ? 'Upload' : 'Send'}
      </Button>

      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        style={{ display: 'none' }}
        accept=".pdf,.docx,.xlsx,.jpg,.jpeg,.png,.txt"
      />
    </Paper>
  );
};

export default ChatInput;