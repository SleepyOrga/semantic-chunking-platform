import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Typography,
  LinearProgress,
  Alert,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Divider,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import VisibilityIcon from '@mui/icons-material/Visibility';
import axios from 'axios';

function App() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState('');
  const [severity, setSeverity] = useState('success');
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const username = 'hanhiho'; // Get from context/auth or hardcode for demo

  useEffect(() => {
    // In a real app, you'd fetch uploaded files from your backend
    // For now, we'll just use local state
  }, []);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setMessage('');
  };

  const handleUpload = async () => {
    if (!file) {
      setSeverity('warning');
      setMessage('Please select a file first.');
      return;
    }
    setUploading(true);
    setMessage('');
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('username', username);

      const res = await axios.post('http://localhost:4000/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setSeverity('success');
      setMessage(`Upload successful!`);
      
      // Add the new file to our list
      setUploadedFiles([
        {
          filename: res.data.filename,
          key: res.data.key,
          uploadedAt: res.data.uploadedAt
        },
        ...uploadedFiles
      ]);
      
      setFile(null);
    } catch (err) {
      setSeverity('error');
      setMessage('Upload failed: ' + (err.response?.data?.message || err.message));
    }
    setUploading(false);
  };

  const handleViewFile = async (key) => {
    try {
      const res = await axios.get(`http://localhost:4000/upload/view/${encodeURIComponent(key)}`);
      window.open(res.data.url, '_blank');
    } catch (err) {
      setSeverity('error');
      setMessage('Failed to retrieve file: ' + err.message);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <Box
      minHeight="100vh"
      display="flex"
      alignItems="center"
      justifyContent="center"
      bgcolor="#f5f5f5"
      p={2}
    >
      <Paper elevation={3} sx={{ p: 4, width: '100%', maxWidth: 600 }}>
        <Typography variant="h5" gutterBottom>
          Document Upload
        </Typography>
        <Box display="flex" flexDirection="column" gap={2}>
          <Button
            variant="contained"
            component="label"
            startIcon={<CloudUploadIcon />}
            disabled={uploading}
          >
            Choose File
            <input
              hidden
              type="file"
              accept=".pdf,.docx,.xlsx,.jpg,.jpeg,.png"
              onChange={handleFileChange}
            />
          </Button>
          {file && (
            <Typography variant="body2" color="text.secondary">
              Selected: {file.name}
            </Typography>
          )}
          <Button
            variant="contained"
            color="primary"
            disabled={!file || uploading}
            onClick={handleUpload}
            sx={{ mb: 2 }}
          >
            {uploading ? 'Uploading...' : 'Upload'}
          </Button>
          {uploading && <LinearProgress sx={{ mb: 2 }} />}
          {message && (
            <Alert severity={severity} sx={{ mb: 2 }}>
              {message}
            </Alert>
          )}

          {/* Uploaded Files List */}
          {uploadedFiles.length > 0 && (
            <>
              <Typography variant="h6" gutterBottom>
                Uploaded Files
              </Typography>
              <List sx={{ width: '100%', bgcolor: 'background.paper' }}>
                {uploadedFiles.map((item, index) => (
                  <React.Fragment key={item.key}>
                    <ListItem alignItems="flex-start">
                      <ListItemText
                        primary={item.filename}
                        secondary={`Uploaded: ${formatDate(item.uploadedAt)}`}
                      />
                      <ListItemSecondaryAction>
                        <IconButton 
                          edge="end" 
                          aria-label="view"
                          onClick={() => handleViewFile(item.key)}
                        >
                          <VisibilityIcon />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                    {index < uploadedFiles.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </>
          )}

          <Box mt={2}>
            <Typography variant="caption" color="text.secondary">
              Current User: {username} | {new Date().toISOString()}
            </Typography>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
}

export default App;