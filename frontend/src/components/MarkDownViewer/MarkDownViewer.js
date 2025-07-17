// New file - src/components/MarkdownViewer/MarkdownViewer.js
import React, { useState, useEffect } from 'react';
import { Box, Typography, CircularProgress, Paper } from '@mui/material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const MarkdownViewer = ({ file }) => {
  const [markdown, setMarkdown] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadMarkdown = async () => {
      if (!file) {
        setMarkdown('');
        return;
      }

      setLoading(true);
      setError(null);

      try {
        // For now, just load the placeholder markdown file
        const response = await fetch('/page_6.md');
        if (!response.ok) {
          throw new Error(`Failed to load document: ${response.statusText}`);
        }
        const text = await response.text();
        setMarkdown(text);
      } catch (err) {
        console.error('Error loading markdown:', err);
        setError(err.message || 'Failed to load document');
      } finally {
        setLoading(false);
      }
    };

    loadMarkdown();
  }, [file]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography color="error" variant="h6">
          Error Loading Document
        </Typography>
        <Typography color="textSecondary">{error}</Typography>
      </Box>
    );
  }

  if (!file) {
    return (
      <Box sx={{ p: 3, textAlign: 'center', color: 'text.secondary' }}>
        <Typography variant="h6">No Document Selected</Typography>
        <Typography variant="body2">
          Select a document from the sidebar to view its content
        </Typography>
      </Box>
    );
  }

  return (
    <Paper 
      elevation={0} 
      sx={{ 
        p: 3, 
        overflow: 'auto', 
        height: '100%',
        bgcolor: '#fff',
        borderRadius: 0
      }}
    >
      <ReactMarkdown 
        remarkPlugins={[remarkGfm]}
        components={{
          img: ({ node, ...props }) => (
            <img 
              style={{ maxWidth: '100%', height: 'auto' }} 
              {...props} 
              alt={props.alt || 'document image'} 
            />
          ),
          h1: ({ node, ...props }) => 
            <Typography variant="h4" gutterBottom component="h1" {...props} />,
          h2: ({ node, ...props }) => 
            <Typography variant="h5" gutterBottom component="h2" {...props} />,
          h3: ({ node, ...props }) => 
            <Typography variant="h6" gutterBottom component="h3" {...props} />,
          p: ({ node, ...props }) => 
            <Typography variant="body1" paragraph component="p" {...props} />
        }}
      >
        {markdown}
      </ReactMarkdown>
    </Paper>
  );
};

export default MarkdownViewer;