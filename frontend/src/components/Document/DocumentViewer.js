// src/components/Document/DocumentViewer.js
import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Tabs,
  Tab,
  Box,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Close as CloseIcon,
  Download as DownloadIcon,
  Visibility as VisibilityIcon
} from '@mui/icons-material';
import DocumentService from '../../services/DocumentService';
import RawViewer from './RawViewer';
import MarkdownViewer from './MarkdownViewer';
import ChunksViewer from './ChunksViewer';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`document-tabpanel-${index}`}
      aria-labelledby={`document-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const DocumentViewer = ({ open, onClose, documentId, documentName }) => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [documentDetails, setDocumentDetails] = useState(null);
  const [rawFile, setRawFile] = useState(null);
  const [markdownContent, setMarkdownContent] = useState('');
  const [chunks, setChunks] = useState([]);
  const [loadedTabs, setLoadedTabs] = useState(new Set());

  useEffect(() => {
    console.log('[DEBUG] useEffect triggered - open:', open, 'documentId:', documentId);
    if (open && documentId) {
      console.log('[DEBUG] Calling loadDocumentDetails');
      loadDocumentDetails();
    } else {
      console.log('[DEBUG] Not calling loadDocumentDetails - conditions not met');
    }
  }, [open, documentId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (open && documentId && !loadedTabs.has(tabValue)) {
      loadTabContent(tabValue);
    }
  }, [tabValue, open, documentId, loadedTabs]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadDocumentDetails = async () => {
    console.log('[DEBUG] loadDocumentDetails called with documentId:', documentId);
    try {
      setLoading(true);
      setError('');
      
      console.log('[DEBUG] About to call DocumentService.getDocumentDetails');
      const details = await DocumentService.getDocumentDetails(documentId);
      console.log('[DEBUG] Document details loaded:', details);
      console.log('[DEBUG] path:', details.path);
      setDocumentDetails(details);
      
      // Load the first tab content
      await loadTabContent(0);
      setLoadedTabs(new Set([0]));
    } catch (err) {
      console.error('[DEBUG] Error loading document details:', err);
      setError(err.message || 'Failed to load document details');
    } finally {
      setLoading(false);
    }
  };

  const loadTabContent = async (tabIndex) => {
    if (loadedTabs.has(tabIndex)) return;

    try {
      setLoading(true);
      setError('');

      switch (tabIndex) {
        case 0: // Raw file
          if (!rawFile) {
            const response = await DocumentService.getRawFile(documentId);
            setRawFile({
              blob: response.data,
              type: response.headers['content-type'] || documentDetails?.mimetype,
              url: URL.createObjectURL(response.data)
            });
          }
          break;
        
        case 1: // Markdown
          if (!markdownContent) {
            const data = await DocumentService.getParsedMarkdown(documentId);
            setMarkdownContent(data.content || '');
          }
          break;
        
        case 2: // Chunks
          if (chunks.length === 0) {
            const data = await DocumentService.getDocumentChunks(documentId);
            setChunks(data.chunks || []);
          }
          break;
        
        default:
          // No content to load for unknown tab
          break;
      }

      setLoadedTabs(prev => new Set([...prev, tabIndex]));
    } catch (err) {
      setError(err.message || `Failed to load ${getTabName(tabIndex)} content`);
    } finally {
      setLoading(false);
    }
  };

  const getTabName = (index) => {
    const names = ['raw file', 'markdown', 'chunks'];
    return names[index] || 'content';
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleDownload = (content, filename, mimeType = 'text/plain') => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleDownloadRaw = () => {
    if (rawFile && documentDetails) {
      const link = document.createElement('a');
      link.href = rawFile.url;
      link.download = documentDetails.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const handleDownloadMarkdown = () => {
    if (markdownContent) {
      handleDownload(markdownContent, `${documentName || 'document'}.md`, 'text/markdown');
    }
  };

  const handleDownloadChunks = () => {
    if (chunks.length > 0) {
      const jsonContent = JSON.stringify(chunks, null, 2);
      handleDownload(jsonContent, `${documentName || 'document'}_chunks.json`, 'application/json');
    }
  };

  const handleClose = () => {
    // Clean up blob URLs
    if (rawFile?.url) {
      URL.revokeObjectURL(rawFile.url);
    }
    
    // Reset state
    setTabValue(0);
    setDocumentDetails(null);
    setRawFile(null);
    setMarkdownContent('');
    setChunks([]);
    setLoadedTabs(new Set());
    setError('');
    
    onClose();
  };

  const isTabDisabled = (tabIndex) => {
    //console.log('[DEBUG] isTabDisabled called for tab:', tabIndex);
    //console.log('[DEBUG] documentDetails:', documentDetails);
    
    if (!documentDetails) {
      //console.log('[DEBUG] No document details, disabling tab');
      return true;
    }
    
    switch (tabIndex) {
      case 0: // Raw file
        const rawDisabled = !documentDetails.path;
        //console.log('[DEBUG] Raw file tab disabled:', rawDisabled, 'path:', documentDetails.path);
        return rawDisabled;
      case 1: // Markdown
        const markdownDisabled = !documentDetails.path;
        //console.log('[DEBUG] Markdown tab disabled:', markdownDisabled, 'path:', documentDetails.path.replace(/\.[^.]+$/, '.md'));
        return markdownDisabled;
      case 2: // Chunks
        //console.log('[DEBUG] Chunks tab always enabled');
        return false; 
      default:
        return false;
    }
  };

  const getTabIcon = (tabIndex) => {
    if (loadedTabs.has(tabIndex)) {
      return <VisibilityIcon fontSize="small" />;
    }
    return null;
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: { minHeight: '80vh', maxHeight: '90vh' }
      }}
    >
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6" component="div">
          {documentName || 'Document Viewer'}
        </Typography>
        <IconButton onClick={handleClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ p: 0 }}>
        {error && (
          <Alert severity="error" sx={{ m: 2 }}>
            {error}
          </Alert>
        )}

        <Paper sx={{ borderRadius: 0 }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            aria-label="document viewer tabs"
            variant="fullWidth"
          >
            <Tab
              label="Raw File"
              disabled={isTabDisabled(0)}
              icon={getTabIcon(0)}
              iconPosition="end"
            />
            <Tab
              label="Parsed Markdown"
              disabled={isTabDisabled(1)}
              icon={getTabIcon(1)}
              iconPosition="end"
            />
            <Tab
              label="Chunks"
              disabled={isTabDisabled(2)}
              icon={getTabIcon(2)}
              iconPosition="end"
            />
          </Tabs>

          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          )}

          <TabPanel value={tabValue} index={0}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Raw File</Typography>
              <Tooltip title="Download raw file">
                <IconButton onClick={handleDownloadRaw} disabled={!rawFile}>
                  <DownloadIcon />
                </IconButton>
              </Tooltip>
            </Box>
            <RawViewer 
              file={rawFile} 
              documentDetails={documentDetails} 
            />
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Parsed Markdown</Typography>
              <Tooltip title="Download markdown">
                <IconButton onClick={handleDownloadMarkdown} disabled={!markdownContent}>
                  <DownloadIcon />
                </IconButton>
              </Tooltip>
            </Box>
            <MarkdownViewer content={markdownContent} />
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Document Chunks</Typography>
              <Tooltip title="Download chunks JSON">
                <IconButton onClick={handleDownloadChunks} disabled={chunks.length === 0}>
                  <DownloadIcon />
                </IconButton>
              </Tooltip>
            </Box>
            <ChunksViewer chunks={chunks} />
          </TabPanel>
        </Paper>
      </DialogContent>

      <DialogActions sx={{ p: 2 }}>
        <Button onClick={handleClose} variant="outlined">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DocumentViewer;
