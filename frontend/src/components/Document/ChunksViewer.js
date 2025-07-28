// src/components/Document/ChunksViewer.js
import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Grid,
  Card,
  CardContent,
  TextField,
  InputAdornment,
  ToggleButton,
  ToggleButtonGroup,
  Divider
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Search as SearchIcon,
  ViewList as ListIcon,
  ViewModule as GridIcon,
  Code as JsonIcon,
  TextSnippet as TextIcon
} from '@mui/icons-material';

const ChunksViewer = ({ chunks }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState('cards');
  const [jsonView, setJsonView] = useState(false);

  if (!chunks || chunks.length === 0) {
    return (
      <Alert severity="info">
        No chunks available for this document. The document may still be processing.
      </Alert>
    );
  }

  const filteredChunks = chunks.filter(chunk =>
    chunk.content?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    chunk.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    chunk.tags?.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleSearchChange = (event) => {
    setSearchTerm(event.target.value);
  };

  const handleViewModeChange = (event, newMode) => {
    if (newMode !== null) {
      setViewMode(newMode);
    }
  };

  const handleJsonToggle = (event, newView) => {
    if (newView !== null) {
      setJsonView(newView);
    }
  };

  const formatChunkContent = (content) => {
    if (!content) return '';
    return content.length > 300 ? content.substring(0, 300) + '...' : content;
  };

  const renderChunkCard = (chunk, index) => (
    <Card key={chunk.id || index} elevation={2} sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Typography variant="h6" component="h3" gutterBottom>
            {chunk.title || `Chunk ${chunk.chunk_index !== undefined ? chunk.chunk_index + 1 : index + 1}`}
          </Typography>
          <Chip 
            label={`#${chunk.chunk_index !== undefined ? chunk.chunk_index : index}`} 
            size="small" 
            color="primary" 
            variant="outlined"
          />
        </Box>

        <Typography variant="body2" color="text.secondary" paragraph>
          {formatChunkContent(chunk.content)}
        </Typography>

        {chunk.tags && chunk.tags.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary" gutterBottom display="block">
              Tags:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {chunk.tags.map((tag, tagIndex) => (
                <Chip
                  key={tagIndex}
                  label={tag}
                  size="small"
                  color="secondary"
                  variant="outlined"
                />
              ))}
            </Box>
          </Box>
        )}

        {chunk.embedding && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            Embedding: {chunk.embedding.length} dimensions
          </Typography>
        )}
      </CardContent>
    </Card>
  );

  const renderChunkList = (chunk, index) => (
    <Accordion key={chunk.id || index}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
          <Typography variant="subtitle1" sx={{ flexGrow: 1 }}>
            {chunk.title || `Chunk ${chunk.chunk_index !== undefined ? chunk.chunk_index + 1 : index + 1}`}
          </Typography>
          <Chip 
            label={`#${chunk.chunk_index !== undefined ? chunk.chunk_index : index}`} 
            size="small" 
            color="primary" 
            sx={{ mr: 2 }}
          />
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        <Typography variant="body2" paragraph sx={{ whiteSpace: 'pre-wrap' }}>
          {chunk.content}
        </Typography>

        {chunk.tags && chunk.tags.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary" gutterBottom display="block">
              Tags:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {chunk.tags.map((tag, tagIndex) => (
                <Chip
                  key={tagIndex}
                  label={tag}
                  size="small"
                  color="secondary"
                  variant="outlined"
                />
              ))}
            </Box>
          </Box>
        )}

        {chunk.embedding && (
          <Typography variant="caption" color="text.secondary">
            Embedding: {chunk.embedding.length} dimensions
          </Typography>
        )}
      </AccordionDetails>
    </Accordion>
  );

  const renderJsonView = () => (
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
        {JSON.stringify(filteredChunks, null, 2)}
      </pre>
    </Paper>
  );

  return (
    <Box>
      {/* Controls */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="body2" color="text.secondary">
            {filteredChunks.length} of {chunks.length} chunks
          </Typography>
          
          <TextField
            size="small"
            placeholder="Search chunks..."
            value={searchTerm}
            onChange={handleSearchChange}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            sx={{ minWidth: 200 }}
          />
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <ToggleButtonGroup
            value={jsonView}
            exclusive
            onChange={handleJsonToggle}
            size="small"
          >
            <ToggleButton value={false}>
              <TextIcon sx={{ mr: 1 }} />
              Text
            </ToggleButton>
            <ToggleButton value={true}>
              <JsonIcon sx={{ mr: 1 }} />
              JSON
            </ToggleButton>
          </ToggleButtonGroup>

          {!jsonView && (
            <ToggleButtonGroup
              value={viewMode}
              exclusive
              onChange={handleViewModeChange}
              size="small"
            >
              <ToggleButton value="cards">
                <GridIcon />
              </ToggleButton>
              <ToggleButton value="list">
                <ListIcon />
              </ToggleButton>
            </ToggleButtonGroup>
          )}
        </Box>
      </Box>

      <Divider sx={{ mb: 3 }} />

      {/* Content */}
      {jsonView ? (
        renderJsonView()
      ) : (
        <Box>
          {filteredChunks.length === 0 ? (
            <Alert severity="info">
              No chunks match your search criteria.
            </Alert>
          ) : viewMode === 'cards' ? (
            <Grid container spacing={2}>
              {filteredChunks.map((chunk, index) => (
                <Grid item xs={12} key={chunk.id || index}>
                  {renderChunkCard(chunk, index)}
                </Grid>
              ))}
            </Grid>
          ) : (
            <Box>
              {filteredChunks.map((chunk, index) => renderChunkList(chunk, index))}
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
};

export default ChunksViewer;
