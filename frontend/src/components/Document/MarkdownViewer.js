// src/components/Document/MarkdownViewer.js
import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Alert,
  ToggleButton,
  ToggleButtonGroup,
  Divider
} from '@mui/material';
import {
  Visibility as PreviewIcon,
  Code as CodeIcon
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const MarkdownViewer = ({ content }) => {
  const [viewMode, setViewMode] = useState('preview');

  if (!content) {
    return (
      <Alert severity="info">
        No parsed markdown available for this document.
      </Alert>
    );
  }

  const handleViewModeChange = (event, newMode) => {
    if (newMode !== null) {
      setViewMode(newMode);
    }
  };

  const renderMarkdownPreview = () => (
    <Paper
      elevation={0}
      sx={{
        p: 3,
        backgroundColor: '#fafafa',
        border: '1px solid #e0e0e0',
        maxHeight: '600px',
        overflow: 'auto',
        '& h1, & h2, & h3, & h4, & h5, & h6': {
          color: '#1976d2',
          marginTop: '1.5em',
          marginBottom: '0.5em'
        },
        '& h1': { fontSize: '2rem', borderBottom: '2px solid #e0e0e0', paddingBottom: '0.3em' },
        '& h2': { fontSize: '1.75rem', borderBottom: '1px solid #e0e0e0', paddingBottom: '0.3em' },
        '& h3': { fontSize: '1.5rem' },
        '& p': { lineHeight: 1.6, marginBottom: '1em' },
        '& ul, & ol': { paddingLeft: '2em', marginBottom: '1em' },
        '& li': { marginBottom: '0.5em' },
        '& blockquote': {
          borderLeft: '4px solid #1976d2',
          paddingLeft: '1em',
          margin: '1em 0',
          backgroundColor: '#f5f5f5',
          fontStyle: 'italic'
        },
        '& code': {
          backgroundColor: '#f5f5f5',
          padding: '0.2em 0.4em',
          borderRadius: '3px',
          fontFamily: 'Monaco, Consolas, "Courier New", monospace',
          fontSize: '0.9em'
        },
        '& pre': {
          backgroundColor: '#f5f5f5',
          padding: '1em',
          borderRadius: '4px',
          overflow: 'auto',
          marginBottom: '1em'
        },
        '& pre code': {
          backgroundColor: 'transparent',
          padding: 0
        },
        '& table': {
          borderCollapse: 'collapse',
          width: '100%',
          marginBottom: '1em'
        },
        '& th, & td': {
          border: '1px solid #ddd',
          padding: '0.5em',
          textAlign: 'left'
        },
        '& th': {
          backgroundColor: '#f5f5f5',
          fontWeight: 'bold'
        },
        '& img': {
          maxWidth: '100%',
          height: 'auto',
          border: '1px solid #ddd',
          borderRadius: '4px',
          marginBottom: '1em'
        }
      }}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <Typography variant="h4" component="h1" gutterBottom>
              {children}
            </Typography>
          ),
          h2: ({ children }) => (
            <Typography variant="h5" component="h2" gutterBottom>
              {children}
            </Typography>
          ),
          h3: ({ children }) => (
            <Typography variant="h6" component="h3" gutterBottom>
              {children}
            </Typography>
          ),
          p: ({ children }) => (
            <Typography variant="body1" component="p" paragraph>
              {children}
            </Typography>
          )
        }}
      >
        {content}
      </ReactMarkdown>
    </Paper>
  );

  const renderMarkdownSource = () => (
    <Paper
      elevation={0}
      sx={{
        backgroundColor: '#f5f5f5',
        border: '1px solid #e0e0e0',
        maxHeight: '600px',
        overflow: 'auto'
      }}
    >
      <pre
        style={{
          margin: 0,
          padding: '1rem',
          fontSize: '0.875rem',
          fontFamily: 'Monaco, Consolas, "Courier New", monospace',
          lineHeight: 1.5,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word'
        }}
      >
        {content}
      </pre>
    </Paper>
  );

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="body2" color="text.secondary">
          {content.split('\n').length} lines • {content.length} characters
        </Typography>
        
        <ToggleButtonGroup
          value={viewMode}
          exclusive
          onChange={handleViewModeChange}
          size="small"
        >
          <ToggleButton value="preview" aria-label="preview">
            <PreviewIcon sx={{ mr: 1 }} />
            Preview
          </ToggleButton>
          <ToggleButton value="source" aria-label="source">
            <CodeIcon sx={{ mr: 1 }} />
            Source
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      <Divider sx={{ mb: 2 }} />

      {viewMode === 'preview' ? renderMarkdownPreview() : renderMarkdownSource()}
    </Box>
  );
};

export default MarkdownViewer;
