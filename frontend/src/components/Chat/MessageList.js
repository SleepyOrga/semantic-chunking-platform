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
      p: 2,
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Welcome message */}
      {messages.length === 0 && (
        <WelcomeScreen onUploadClick={onUploadClick} />
      )}

      {/* Messages */}
      {messages.map((message, index) => (
        <Message key={index} message={message} />
      ))}
      
      {/* Auto-scroll anchor */}
      <div ref={messagesEndRef} />
      
      {/* Loading indicator */}
      {isLoading && <LoadingIndicator />}
    </Box>
  );
};

export default MessageList;