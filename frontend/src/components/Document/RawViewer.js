// src/components/Document/RawViewer.js
import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  PictureAsPdf as PdfIcon,
  Description as DocIcon,
  TableChart as ExcelIcon,
  Image as ImageIcon,
  InsertDriveFile as FileIcon
} from '@mui/icons-material';

const RawViewer = ({ file, documentDetails }) => {
  if (!file || !documentDetails) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  const getFileIcon = (mimetype) => {
    if (mimetype?.includes('pdf')) return <PdfIcon sx={{ fontSize: 48, color: '#d32f2f' }} />;
    if (mimetype?.includes('word') || mimetype?.includes('docx')) return <DocIcon sx={{ fontSize: 48, color: '#1976d2' }} />;
    if (mimetype?.includes('sheet') || mimetype?.includes('xlsx')) return <ExcelIcon sx={{ fontSize: 48, color: '#388e3c' }} />;
    if (mimetype?.includes('image')) return <ImageIcon sx={{ fontSize: 48, color: '#f57c00' }} />;
    return <FileIcon sx={{ fontSize: 48, color: '#757575' }} />;
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const canPreview = () => {
    const mimetype = file.type || documentDetails.mimetype;
    return mimetype?.includes('image') || mimetype?.includes('pdf');
  };

  const renderPreview = () => {
    const mimetype = file.type || documentDetails.mimetype;
    
    if (mimetype?.includes('image')) {
      return (
        <Box sx={{ textAlign: 'center', mt: 2 }}>
          <img
            src={file.url}
            alt={documentDetails.filename}
            style={{
              maxWidth: '100%',
              maxHeight: '400px',
              objectFit: 'contain',
              border: '1px solid #ddd',
              borderRadius: '4px'
            }}
          />
        </Box>
      );
    }

    if (mimetype?.includes('pdf')) {
      return (
        <Box sx={{ mt: 2, height: '500px' }}>
          <iframe
            src={file.url}
            width="100%"
            height="100%"
            style={{ border: '1px solid #ddd', borderRadius: '4px' }}
            title="PDF Preview"
          >
            <Alert severity="info">
              Your browser doesn't support PDF preview. 
              <a href={file.url} target="_blank" rel="noopener noreferrer">
                Click here to view the PDF
              </a>
            </Alert>
          </iframe>
        </Box>
      );
    }

    return null;
  };

  return (
    <Box>
      <Paper 
        elevation={1} 
        sx={{ 
          p: 3, 
          mb: 3, 
          display: 'flex', 
          alignItems: 'center',
          backgroundColor: '#f5f5f5'
        }}
      >
        <Box sx={{ mr: 3 }}>
          {getFileIcon(documentDetails.mimetype)}
        </Box>
        
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h6" gutterBottom>
            {documentDetails.filename}
          </Typography>
          
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Type: {documentDetails.mimetype}
          </Typography>
          
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Size: {formatFileSize(documentDetails.size)}
          </Typography>
          
          <Typography variant="body2" color="text.secondary">
            Uploaded: {new Date(documentDetails.created_at).toLocaleString()}
          </Typography>
        </Box>
      </Paper>

      {canPreview() ? (
        <>
          <Typography variant="subtitle1" gutterBottom>
            Preview:
          </Typography>
          {renderPreview()}
        </>
      ) : (
        <Alert severity="info" sx={{ mt: 2 }}>
          Preview not available for this file type. 
          You can download the file to view its contents.
        </Alert>
      )}
    </Box>
  );
};

export default RawViewer;
