import React from 'react';
import { Box, Typography, Paper, CircularProgress, Divider, Chip } from '@mui/material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const Message = ({ message }) => {
  const isUser = message.type === 'user';
  
  // For interim messages (chunk summary with actual chunks displayed)
  if (message.isInterim && message.chunks) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'flex-start',
          mb: 2,
          width: '100%'
        }}
      >
        <Paper
          elevation={1}
          sx={{
            p: 2,
            maxWidth: '95%',
            backgroundColor: '#f0f7ff',
            borderRadius: 2,
            width: '100%'
          }}
        >
          <Typography variant="body1" sx={{ mb: 1, fontWeight: 'bold' }}>
            {message.content}
          </Typography>
          
          <Box sx={{ maxHeight: '300px', overflowY: 'auto', mb: 2 }}>
            {message.chunks.map((chunk, index) => (
              <Box key={index} sx={{ mb: 2, p: 1, backgroundColor: 'rgba(0,0,0,0.03)', borderRadius: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Chip 
                    label={`Passage ${index + 1}`} 
                    size="small" 
                    color="primary" 
                    variant="outlined"
                  />
                  <Chip 
                    label={`Score: ${Math.round(chunk.score * 100)}%`} 
                    size="small" 
                    color={chunk.score > 0.7 ? "success" : "default"}
                    variant="outlined"
                  />
                </Box>
                <Typography variant="body2">
                  {chunk.content}
                </Typography>
              </Box>
            ))}
          </Box>
          
          <Divider sx={{ my: 1 }} />
          
          <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
            <CircularProgress size={16} sx={{ mr: 1 }} />
            <Typography variant="caption" color="text.secondary">
              Generating response based on these passages...
            </Typography>
          </Box>
        </Paper>
      </Box>
    );
  }
  
  // For streaming messages
  if (message.isStreaming) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: isUser ? 'flex-end' : 'flex-start',
          mb: 2,
        }}
      >
        <Paper
          elevation={1}
          sx={{
            p: 2,
            maxWidth: '80%',
            backgroundColor: isUser ? '#e3f2fd' : '#ffffff',
            borderRadius: 2,
          }}
        >
          {message.content ? (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          ) : (
            <Typography variant="body2" color="text.secondary">
              Thinking...
            </Typography>
          )}
          
          {message.isError ? (
            <Box sx={{ mt: 1, color: 'error.main' }}>
              <Typography variant="caption">
                {message.errorMessage || "Error generating response. Please try again."}
              </Typography>
            </Box>
          ) : (
            <Box sx={{ display: 'flex', mt: message.content ? 1 : 0 }}>
              <CircularProgress size={12} sx={{ mr: 0.5 }} />
              <CircularProgress size={12} sx={{ mr: 0.5, animationDelay: '0.2s' }} />
              <CircularProgress size={12} sx={{ animationDelay: '0.4s' }} />
            </Box>
          )}
        </Paper>
      </Box>
    );
  }
  
  // Regular message (existing code)
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        mb: 2,
      }}
    >
      <Paper
        elevation={1}
        sx={{
          p: 2,
          maxWidth: '80%',
          backgroundColor: isUser ? '#e3f2fd' : '#ffffff',
          borderRadius: 2,
          ...(message.error && { backgroundColor: '#ffebee' }),
        }}
      >
        {message.isFile ? (
          <Box>
            <Typography variant="body1">{message.content}</Typography>
            {message.file && (
              <Box sx={{ mt: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  {message.file.name} ({(message.file.size / 1024).toFixed(1)} KB)
                </Typography>
              </Box>
            )}
          </Box>
        ) : (
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        )}
      </Paper>
    </Box>
  );
};

export default Message;