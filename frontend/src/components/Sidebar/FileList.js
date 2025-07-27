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
import DescriptionIcon from '@mui/icons-material/Description';
import TableChartIcon from '@mui/icons-material/TableChart';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';

const FileList = ({ files, onDeleteFile, onViewFile }) => {
  const getFileIcon = (mimetype) => {
    if (mimetype.includes('pdf')) return <PictureAsPdfIcon color="error" />;
    if (mimetype.includes('image')) return <ImageIcon color="primary" />;
    if (mimetype.includes('word') || mimetype.includes('document')) 
      return <DescriptionIcon color="primary" />;
    if (mimetype.includes('sheet') || mimetype.includes('excel'))
      return <TableChartIcon color="success" />;
    return <InsertDriveFileIcon color="action" />;
  };

  return (
    <List sx={{ overflowY: 'auto', flexGrow: 1 }}>
      {files.map((item) => (
        <ListItem 
          key={item.id} 
          sx={{ 
            borderBottom: '1px solid #f0f0f0',
            '&:hover': { bgcolor: '#f5f5f5' },
            pr: 6 // Extra padding for action buttons
          }}
        >
          <ListItemAvatar>
            <Avatar sx={{ bgcolor: '#f0f0f0' }}>
              {getFileIcon(item.mimetype)}
            </Avatar>
          </ListItemAvatar>
          <ListItemText 
            primary={item.filename} 
            secondary={`Uploaded: ${new Date(item.uploadedAt).toLocaleString()}`}
            primaryTypographyProps={{ 
              noWrap: true,
              style: { 
                maxWidth: '120px',
                fontWeight: '500'
              }
            }}
          />
          <ListItemSecondaryAction>
            <Box sx={{ display: 'flex', gap: 0.5 }}>
              <Tooltip title="View document">
                <IconButton 
                  edge="end" 
                  size="small"
                  onClick={() => onViewFile(item)}
                >
                  <VisibilityIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title="Delete document">
                <IconButton 
                  edge="end" 
                  size="small"
                  onClick={() => onDeleteFile(item.id)}
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

export default FileList;