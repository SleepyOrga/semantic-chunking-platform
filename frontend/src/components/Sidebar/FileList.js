// src/components/Sidebar/FileList.js
import React from 'react';
import {
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  ListItemSecondaryAction,
  IconButton,
  Tooltip,
  Box
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import VisibilityIcon from '@mui/icons-material/Visibility';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import ImageIcon from '@mui/icons-material/Image';
import TableChartIcon from '@mui/icons-material/TableChart';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';
import TextSnippetIcon from '@mui/icons-material/TextSnippet';
import ArticleIcon from '@mui/icons-material/Article';
import PhotoIcon from '@mui/icons-material/Photo';
import MovieIcon from '@mui/icons-material/Movie';
import AudioFileIcon from '@mui/icons-material/AudioFile';
import CodeIcon from '@mui/icons-material/Code';
import GridOnIcon from '@mui/icons-material/GridOn';

const FileList = ({ files, onDeleteFile, onViewFile }) => {
  const getFileIcon = (mimetype, filename = '') => {
    const extension = filename.toLowerCase().split('.').pop();
    console.log(`File: ${filename}, Extension: ${extension}, MIME Type: ${mimetype}`);

    // PDF files
    if (mimetype.includes('pdf'))
      return <PictureAsPdfIcon sx={{ color: '#d32f2f' }} />;

    // Image files
    if (mimetype.includes('image')) {
      if (extension === 'jpg' || extension === 'jpeg')
        return <PhotoIcon sx={{ color: '#ff9800' }} />;
      if (extension === 'png')
        return <ImageIcon sx={{ color: '#4caf50' }} />;
      return <ImageIcon sx={{ color: '#2196f3' }} />;
    }

    // Spreadsheet files
    if (extension === 'xlsx' || extension === 'xls') {
      console.log(`Detected Excel file: ${filename}`);
      return <img src="/sheets.png" alt="Excel" style={{ width: 24, height: 24 }} />;
    }

    // Document files
    if (extension === 'docx')
      return <ArticleIcon sx={{ color: '#1976d2' }} />;


    // CSV files
    if (extension === 'csv')
      return <TableChartIcon sx={{ color: '#4caf50' }} />;

    // Text files
    if (mimetype.includes('text') || extension === 'txt')
      return <TextSnippetIcon sx={{ color: '#666' }} />;

    // Code files
    if (['js', 'ts', 'jsx', 'tsx', 'py', 'java', 'cpp', 'c', 'html', 'css', 'json'].includes(extension))
      return <CodeIcon sx={{ color: '#ff5722' }} />;

    // Default
    return <InsertDriveFileIcon sx={{ color: '#757575' }} />;
  };

  return (
    <List
      sx={{
        overflowY: 'auto',
        flexGrow: 1,
        px: 2,
        py: 1,
      }}
    >
      {files.map((item, index) => (
        <ListItem
          key={item.id}
          sx={{
            mb: 1.5,
            borderRadius: 2,
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            background: 'white',
            border: '1px solid rgba(0,0,0,0.04)',
            animation: `fadeIn 0.3s ease-out ${index * 0.1}s forwards`,
            opacity: 0,
            '@keyframes fadeIn': {
              '0%': { opacity: 0, transform: 'translateY(10px)' },
              '100%': { opacity: 1, transform: 'translateY(0)' }
            },
            '&:hover': {
              bgcolor: 'rgba(88, 167, 254, 0.05)',
              boxShadow: '0 3px 10px rgba(0,0,0,0.08)',
              transform: 'translateY(-2px)',
              '& .MuiListItemText-primary': {
                color: 'primary.main'
              },
              '& .MuiAvatar-root': {
                transform: 'scale(1.1)',
                transition: 'transform 0.3s ease'
              }
            },
            pr: 8, // Extra padding for action buttons
            transition: 'all 0.3s ease'
          }}
        >
          <ListItemAvatar>
            <Avatar
              sx={{
                bgcolor: 'rgba(0,0,0,0.03)',
                p: 0.5,
                borderRadius: 2,
                boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.08)',
                transition: 'all 0.3s ease',
              }}
            >
              {getFileIcon(item.mimetype, item.filename)}
            </Avatar>
          </ListItemAvatar>
          <ListItemText
            primary={item.filename}
            secondary={`Uploaded: ${formatDate(item.uploadedAt)}`}
            primaryTypographyProps={{
              noWrap: true,
              style: {
                maxWidth: '160px',
                fontWeight: '600',
                fontSize: '0.95rem'
              }
            }}
            secondaryTypographyProps={{
              sx: {
                fontSize: '0.75rem',
                color: 'text.secondary',
                mt: 0.5,
                maxWidth: '150px',
                whiteSpace: 'pre-line', 
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }
            }}
          />

          <ListItemSecondaryAction>
            <Box sx={{ display: 'flex', gap: 1, position: 'center', right: 8 }}>
              <Tooltip title="View document" arrow>
                <IconButton
                  edge="end"
                  size="small"
                  onClick={() => onViewFile(item)}
                  sx={{
                    bgcolor: 'rgba(88, 167, 254, 0.08)',
                    '&:hover': {
                      bgcolor: 'primary.main',
                      color: 'white',
                      transform: 'scale(1.1)'
                    },
                    transition: 'all 0.2s ease'
                  }}
                >
                  <VisibilityIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title="Delete document" arrow>
                <IconButton
                  edge="end"
                  size="small"
                  onClick={() => onDeleteFile(item.id)}
                  sx={{
                    bgcolor: 'rgba(244, 67, 54, 0.08)',
                    '&:hover': {
                      bgcolor: '#f44336',
                      color: 'white',
                      transform: 'scale(1.1)'
                    },
                    transition: 'all 0.2s ease'
                  }}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          </ListItemSecondaryAction>
        </ListItem>
      ))}
    </List>
  );
};

const formatDate = (dateStr) => {
  const date = new Date(dateStr);
  const datePart = date.toLocaleDateString();     // e.g., "8/1/2025"
  const timePart = date.toLocaleTimeString();     // e.g., "4:01:49 PM"
  return `${datePart}\n${timePart}`;
};


export default FileList;