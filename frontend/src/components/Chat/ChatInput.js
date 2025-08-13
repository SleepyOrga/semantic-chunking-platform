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
  fileInputRef,
  onFileChange
}) => {
  return (
    <Paper 
      component="form" 
      onSubmit={onSubmit}
      elevation={0}
      sx={{ 
        p: { xs: 1.5, sm: 2, md: 2.5 },
        display: 'flex', 
        alignItems: 'center',
        position: 'relative',
        bgcolor: 'transparent',
        borderRadius: '16px',
        mx: { xs: 1, sm: 2 },
        mb: { xs: 1, sm: 2 },
        transition: 'all 0.3s ease',
      }}
    >
      {/* File preview */}
      <FilePreview file={file} onClear={onClearFile} />

      {/* File input (hidden) */}
      <input
        type="file"
        ref={fileInputRef}
        style={{ display: 'none' }}
        onChange={onFileChange}
        accept=".pdf,.docx,.xlsx,.jpg,.jpeg,.png,.txt"
      />

      {/* File upload button */}
      <IconButton 
        onClick={onFileButtonClick}
        disabled={isLoading}
        sx={{
          background: 'linear-gradient(45deg, rgba(127, 231, 134, 0.1), rgba(88, 167, 254, 0.1))',
          color: 'grey.800',
          borderRadius: '12px',
          p: 1.2,
          mr: 1,
          transition: 'all 0.2s ease',
          border: '1px solid rgba(88, 167, 254, 0.15)',
          '&:hover': {
            background: 'linear-gradient(45deg, rgba(127, 231, 134, 0.2), rgba(88, 167, 254, 0.2))',
            transform: 'translateY(-2px)',
            boxShadow: '0 4px 10px rgba(88, 167, 254, 0.15)',
          },
          '&:disabled': {
            background: 'rgba(0,0,0,0.03)',
            color: 'rgba(0,0,0,0.3)',
          }
        }}
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
            borderRadius: '12px',
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            boxShadow: '0 4px 15px rgba(0, 0, 0, 0.05)',
            border: '1px solid rgba(0, 0, 0, 0.04)',
            transition: 'all 0.3s ease',
            '&:hover': {
              boxShadow: '0 5px 20px rgba(0, 0, 0, 0.08)',
            },
            '&.Mui-focused': {
              boxShadow: '0 5px 20px rgba(88, 167, 254, 0.15)',
            },
          },
          '& .MuiOutlinedInput-notchedOutline': {
            borderColor: 'transparent',
          },
          '& .MuiInputBase-input': {
            py: 1.5,
          },
        }}
      />

      {/* Send button */}
      <Button
        variant="contained"
        endIcon={<SendIcon />}
        disabled={isLoading || (!input.trim() && !file)}
        type="submit"
        sx={{ 
          borderRadius: '12px',
          px: 2.5,
          py: 1.2,
          background: 'linear-gradient(45deg, #7FE786, #58A7FE)',
          boxShadow: '0 4px 15px rgba(88, 167, 254, 0.3)',
          textTransform: 'none',
          fontWeight: 600,
          transition: 'all 0.3s ease',
          '&:hover': {
            background: 'linear-gradient(45deg, #6BD673, #4592E6)',
            boxShadow: '0 6px 20px rgba(88, 167, 254, 0.4)',
            transform: 'translateY(-2px)',
          },
          '&:active': {
            transform: 'translateY(0px)',
            boxShadow: '0 2px 10px rgba(88, 167, 254, 0.3)',
          },
          '&:disabled': {
            background: 'linear-gradient(45deg, #e0e0e0, #d5d5d5)',
            boxShadow: 'none',
            color: 'rgba(0, 0, 0, 0.3)',
          }
        }}
      >
        {file ? 'Upload' : 'Send'}
      </Button>
    </Paper>
  );
};

export default ChatInput;