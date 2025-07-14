// src/pages/HomePage.js
import React, { useState, useRef, useEffect } from 'react';
import { Box, useMediaQuery } from '@mui/material';
import Header from '../components/Header/Header';
import Sidebar from '../components/Sidebar/SideBar';
import MessageList from '../components/Chat/MessageList';
import ChatInput from '../components/Chat/ChatInput';
import ErrorAlert from '../components/Common/ErrorAlert';
import DocumentService from '../services/DocumentService';
import SearchService from '../services/SearchService';
import AuthService from '../services/AuthService';
import { useNavigate } from 'react-router-dom';

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

const HomePage = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const isMobile = useMediaQuery('(max-width:768px)');
  const navigate = useNavigate();
  
  // Check if user is authenticated
  useEffect(() => {
    if (!AuthService.isAuthenticated()) {
      navigate('/auth');
    } else {
      // Load user's documents
      loadUserDocuments();
    }
  }, [navigate]);
  
  // Load user documents
  const loadUserDocuments = async () => {
    try {
      setIsLoading(true);
      const data = await DocumentService.getUserDocuments();
      console.log("Loaded documents:", data);
      setUploadedFiles(data.documents || []);
    } catch (err) {
      setError('Failed to load documents. Please refresh the page.');
    } finally {
      setIsLoading(false);
    }
  };

  // Close sidebar automatically on mobile
  useEffect(() => {
    if (isMobile) {
      setSidebarOpen(false);
    } else {
      setSidebarOpen(true);
    }
  }, [isMobile]);

  // Scroll to bottom whenever messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle input change
  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  // Handle file selection
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    if (selectedFile.size > MAX_FILE_SIZE) {
      setError(`File size exceeds the limit (10MB). Selected file is ${(selectedFile.size / (1024 * 1024)).toFixed(2)}MB`);
      return;
    }

    setFile(selectedFile);
    setError('');
  };

  // Clear selected file
  const clearFile = () => {
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Handle file upload
  const handleFileUpload = async () => {
    if (!file) return;

    setIsLoading(true);
    setError('');

    try {
      // Add a user message showing the file upload
      setMessages(prev => [...prev, {
        type: 'user',
        content: `Uploading file: ${file.name}`,
        isFile: true,
        file: file
      }]);

      const user = AuthService.getCurrentUser();
      const response = await DocumentService.uploadDocument(file, user.id);

      // Add uploaded file to list
      setUploadedFiles(prev => [
        ...prev,
        {
          id: response.document_id,
          filename: file.name,
          mimetype: file.type,
          uploadedAt: new Date().toISOString()
        }
      ]);

      // Add assistant response
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: `I've processed your file "${file.name}". You can now ask questions about its content.`,
        isFile: false
      }]);

      // Open sidebar to show the newly uploaded file (especially on mobile)
      if (isMobile) setSidebarOpen(true);

      clearFile();
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.message || 'Error uploading file. Please try again.');
      
      // Add error message
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: `I couldn't process your file. ${err.message || 'Please try again.'}`,
        isFile: false,
        error: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle deleting a file
  const handleDeleteFile = async (fileId) => {
    try {
      await DocumentService.deleteDocument(fileId);
      
      // Remove from local state
      setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
      
      // Add system message
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: 'The document has been removed.',
        isFile: false
      }]);
    } catch (err) {
      console.error('Delete error:', err);
      setError('Failed to delete the file. Please try again.');
    }
  };

  // Handle sending a message/query
  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!input.trim() && !file) return;

    // If there's a file, upload it first
    if (file) {
      await handleFileUpload();
      return;
    }

    const query = input.trim();
    setInput('');
    setIsLoading(true);

    // Add user message
    setMessages(prev => [...prev, {
      type: 'user',
      content: query,
      isFile: false
    }]);

    try {
      // Call semantic search API
      const response = await SearchService.searchDocuments(query);

      // Add assistant response
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: response.result || 'I found no relevant information for your query.',
        isFile: false
      }]);
    } catch (err) {
      console.error('Search error:', err);
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: 'I encountered an error while searching. Please try again.',
        isFile: false,
        error: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Toggle sidebar
  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };
  
  const handleFileButtonClick = () => {
    fileInputRef.current.click();
  };

  return (
    <Box sx={{ 
      height: '100vh', 
      display: 'flex',
      overflow: 'hidden'
    }}>
      {/* Sidebar Component */}
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        isMobile={isMobile}
        files={uploadedFiles}
        onDeleteFile={handleDeleteFile}
        onUploadClick={handleFileButtonClick}
      />
      
      {/* Main content */}
      <Box sx={{ 
        flexGrow: 1, 
        display: 'flex', 
        flexDirection: 'column',
        height: '100%',
        bgcolor: '#f5f7fb'
      }}>
        {/* Header Component */}
        <Header
          sidebarOpen={sidebarOpen}
          toggleSidebar={toggleSidebar}
          documentCount={uploadedFiles.length}
        />

        {/* MessageList Component */}
        <MessageList
          messages={messages}
          isLoading={isLoading}
          onUploadClick={handleFileButtonClick}
          messagesEndRef={messagesEndRef}
        />

        {/* Error Alert Component */}
        <ErrorAlert
          error={error}
          onClose={() => setError('')}
        />

        {/* ChatInput Component */}
        <ChatInput
          input={input}
          onInputChange={handleInputChange}
          onSubmit={handleSendMessage}
          file={file}
          onFileButtonClick={handleFileButtonClick}
          onClearFile={clearFile}
          isLoading={isLoading}
          fileInputRef={fileInputRef}
          onFileChange={handleFileChange}
        />
      </Box>
    </Box>
  );
};

export default HomePage;