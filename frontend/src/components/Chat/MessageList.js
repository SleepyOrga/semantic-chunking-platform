// src/components/Chat/MessageList.js
import React from 'react';
import { Box } from '@mui/material';
import Message from './Message';
import WelcomeScreen from './WelcomeScreen';
import LoadingIndicator from '../Common/LoadingIndicator';

const MessageList = ({ messages, isLoading, onUploadClick, messagesEndRef }) => {
  return (
    <Box sx={{ 
      flexGrow: 1, 
      overflow: 'auto', 
      p: { xs: 1.5, sm: 2, md: 3 },
      display: 'flex',
      flexDirection: 'column',
      scrollBehavior: 'smooth',
      '&::-webkit-scrollbar': {
        width: '8px',
        height: '8px',
      },
      '&::-webkit-scrollbar-track': {
        background: 'transparent',
      },
      '&::-webkit-scrollbar-thumb': {
        background: 'rgba(0,0,0,0.1)',
        borderRadius: '10px',
        '&:hover': {
          background: 'rgba(0,0,0,0.2)',
        },
      },
    }}>
      {/* Welcome message with animation */}
      {messages.length === 0 && (
        <Box sx={{ 
          animation: 'fadeInUp 0.8s ease-out',
          '@keyframes fadeInUp': {
            '0%': { opacity: 0, transform: 'translateY(40px)' },
            '100%': { opacity: 1, transform: 'translateY(0)' }
          }
        }}>
          <WelcomeScreen onUploadClick={onUploadClick} />
        </Box>
      )}

      {/* Messages with staggered animation */}
      {messages.map((message, index) => (
        <Box
          key={index}
          sx={{
            animation: 'fadeIn 0.5s ease-out',
            animationDelay: `${index * 0.1}s`,
            opacity: 1,
            '@keyframes fadeIn': {
              '0%': { opacity: 0, transform: 'translateY(10px)' },
              '100%': { opacity: 1, transform: 'translateY(0)' }
            }
          }}
        >
          <Message message={message} />
        </Box>
      ))}
      
      {/* Auto-scroll anchor */}
      <div ref={messagesEndRef} />
      
      {/* Loading indicator with enhanced styling */}
      {isLoading && (
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'center',
          my: 2,
          animation: 'pulseIn 0.5s ease-out',
          '@keyframes pulseIn': {
            '0%': { opacity: 0, transform: 'scale(0.9)' },
            '100%': { opacity: 1, transform: 'scale(1)' }
          }
        }}>
          <LoadingIndicator />
        </Box>
      )}
    </Box>
  );
};

export default MessageList;