// src/App.js
import React, { useState, useRef, useEffect } from "react";
import "./App.css";
import {
  Box,
  TextField,
  Button,
  Typography,
  Paper,
  Avatar,
  CircularProgress,
  IconButton,
  Divider,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  ListItemSecondaryAction,
  Drawer,
  useMediaQuery,
  Tooltip,
  Badge,
} from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import AttachFileIcon from "@mui/icons-material/AttachFile";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import PersonIcon from "@mui/icons-material/Person";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import InsertDriveFileIcon from "@mui/icons-material/InsertDriveFile";
import CloseIcon from "@mui/icons-material/Close";
import DeleteIcon from "@mui/icons-material/Delete";
import MenuIcon from "@mui/icons-material/Menu";
import FolderIcon from "@mui/icons-material/Folder";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdf";
import ImageIcon from "@mui/icons-material/Image";
import DescriptionIcon from "@mui/icons-material/Description";
import axios from "axios";

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const SIDEBAR_WIDTH = 280; // Width of the sidebar

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const username = "User"; // In a real app, get this from auth
  const isMobile = useMediaQuery("(max-width:768px)");

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
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Get appropriate icon for file type
  const getFileIcon = (mimetype) => {
    if (mimetype.includes("pdf")) return <PictureAsPdfIcon color="error" />;
    if (mimetype.includes("image")) return <ImageIcon color="primary" />;
    if (mimetype.includes("word") || mimetype.includes("document"))
      return <DescriptionIcon color="primary" />;
    return <InsertDriveFileIcon color="action" />;
  };

  // Handle input change
  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  // Handle file selection
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    if (selectedFile.size > MAX_FILE_SIZE) {
      setError(
        `File size exceeds the limit (10MB). Selected file is ${(
          selectedFile.size /
          (1024 * 1024)
        ).toFixed(2)}MB`
      );
      return;
    }

    setFile(selectedFile);
    setError("");
  };

  // Clear selected file
  const clearFile = () => {
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // Handle file upload
  const handleFileUpload = async () => {
    if (!file) return;

    setIsLoading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("username", username);
      formData.append("user_id", "05b207af-8ea7-4a72-8c37-f5723303d01e"); // In a real app, use actual user ID

      // Add a user message showing the file upload
      setMessages((prev) => [
        ...prev,
        {
          type: "user",
          content: `Uploading file: ${file.name}`,
          isFile: true,
          file: file,
        },
      ]);

      const response = await axios.post(
        process.env.REACT_APP_UPLOAD_API_URL || "http://localhost:4000/upload",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );

      // Add uploaded file to list
      setUploadedFiles((prev) => [
        ...prev,
        {
          id: response.data.document_id,
          filename: file.name,
          mimetype: file.type,
          uploadedAt: new Date().toISOString(),
        },
      ]);

      // Add assistant response
      setMessages((prev) => [
        ...prev,
        {
          type: "assistant",
          content: `I've processed your file "${file.name}". You can now ask questions about its content.`,
          isFile: false,
        },
      ]);

      // Open sidebar to show the newly uploaded file (especially on mobile)
      if (isMobile) setSidebarOpen(true);

      clearFile();
    } catch (err) {
      console.error("Upload error:", err);
      setError(
        err.response?.data?.message || "Error uploading file. Please try again."
      );

      // Add error message
      setMessages((prev) => [
        ...prev,
        {
          type: "assistant",
          content: `I couldn't process your file. ${
            err.response?.data?.message || "Please try again."
          }`,
          isFile: false,
          error: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle deleting a file
  const handleDeleteFile = async (fileId) => {
    try {
      // In a real app, make an API call to delete the file
      // await axios.delete(`${process.env.REACT_APP_API_URL}/documents/${fileId}`);

      // Remove from local state
      setUploadedFiles((prev) => prev.filter((f) => f.id !== fileId));

      // Add system message
      setMessages((prev) => [
        ...prev,
        {
          type: "assistant",
          content: "The document has been removed.",
          isFile: false,
        },
      ]);
    } catch (err) {
      console.error("Delete error:", err);
      setError("Failed to delete the file. Please try again.");
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
    setInput("");
    setIsLoading(true);

    // Add user message
    setMessages((prev) => [
      ...prev,
      {
        type: "user",
        content: query,
        isFile: false,
      },
    ]);

    try {
      // Call semantic search API
      const response = await axios.post(
        process.env.REACT_APP_SEARCH_API_URL || "http://localhost:4000/search",
        { query, username }
      );

      // Add assistant response
      setMessages((prev) => [
        ...prev,
        {
          type: "assistant",
          content:
            response.data.result ||
            "I found no relevant information for your query.",
          isFile: false,
        },
      ]);
    } catch (err) {
      console.error("Search error:", err);
      setMessages((prev) => [
        ...prev,
        {
          type: "assistant",
          content: "I encountered an error while searching. Please try again.",
          isFile: false,
          error: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Toggle sidebar
  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <Box
      sx={{
        height: "100vh",
        display: "flex",
        overflow: "hidden",
      }}
    >
      {/* Sidebar */}
      <Drawer
        variant={isMobile ? "temporary" : "persistent"}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        sx={{
          width: SIDEBAR_WIDTH,
          flexShrink: 0,
          "& .MuiDrawer-paper": {
            width: SIDEBAR_WIDTH,
            boxSizing: "border-box",
            borderRight: "1px solid #e0e0e0",
            backgroundColor: "#f8f9fa",
          },
        }}
      >
        <Box
          sx={{
            p: 2,
            display: "flex",
            alignItems: "center",
            borderBottom: "1px solid #e0e0e0",
            bgcolor: "#f0f2f5",
          }}
        >
          <FolderIcon sx={{ mr: 1, color: "#6e41e2" }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            My Documents
          </Typography>
          <IconButton onClick={toggleSidebar} sx={{ display: { sm: "none" } }}>
            <CloseIcon />
          </IconButton>
        </Box>

        {uploadedFiles.length === 0 ? (
          <Box
            sx={{
              p: 3,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              height: "50%",
            }}
          >
            <UploadFileIcon sx={{ fontSize: 60, color: "#c7c7c7", mb: 2 }} />
            <Typography variant="body2" color="text.secondary" align="center">
              No documents uploaded yet
            </Typography>
            <Button
              variant="outlined"
              startIcon={<AttachFileIcon />}
              onClick={() => fileInputRef.current.click()}
              sx={{ mt: 2 }}
            >
              Upload Document
            </Button>
          </Box>
        ) : (
          <List sx={{ overflowY: "auto", flexGrow: 1 }}>
            {uploadedFiles.map((item) => (
              <ListItem
                key={item.id}
                sx={{
                  borderBottom: "1px solid #f0f0f0",
                  "&:hover": { bgcolor: "#f5f5f5" },
                }}
              >
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: "#f0f0f0" }}>
                    {getFileIcon(item.mimetype)}
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={item.filename}
                  secondary={`Uploaded: ${new Date(
                    item.uploadedAt
                  ).toLocaleString()}`}
                  primaryTypographyProps={{
                    noWrap: true,
                    style: {
                      maxWidth: "160px",
                      fontWeight: "500",
                    },
                  }}
                />
                <ListItemSecondaryAction>
                  <Tooltip title="Remove document">
                    <IconButton
                      edge="end"
                      size="small"
                      onClick={() => handleDeleteFile(item.id)}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        )}
      </Drawer>

      {/* Main content */}
      <Box
        sx={{
          flexGrow: 1,
          display: "flex",
          flexDirection: "column",
          height: "100%",
          bgcolor: "#f5f7fb",
        }}
      >
        {/* Header */}
        <Box
          sx={{
            p: 2,
            borderBottom: "1px solid #e0e0e0",
            bgcolor: "white",
            display: "flex",
            alignItems: "center",
          }}
        >
          {!sidebarOpen && (
            <IconButton
              onClick={toggleSidebar}
              sx={{ mr: 1 }}
              aria-label="Open documents sidebar"
            >
              <Badge
                badgeContent={uploadedFiles.length}
                color="primary"
                invisible={uploadedFiles.length === 0}
              >
                <MenuIcon />
              </Badge>
            </IconButton>
          )}
          <AutoAwesomeIcon sx={{ mr: 1, color: "#6e41e2" }} />
          <Typography variant="h6" component="div">
            Semantic Search Assistant
          </Typography>
        </Box>

        {/* Main chat area */}
        <Box
          sx={{
            flexGrow: 1,
            overflow: "auto",
            p: 2,
            display: "flex",
            flexDirection: "column",
          }}
        >
          {/* Welcome message */}
          {messages.length === 0 && (
            <Box
              sx={{
                textAlign: "center",
                maxWidth: "600px",
                mx: "auto",
                my: 4,
                p: 3,
                bgcolor: "white",
                borderRadius: 2,
                boxShadow: 1,
              }}
            >
              <UploadFileIcon sx={{ fontSize: 60, color: "#6e41e2", mb: 2 }} />
              <Typography variant="h5" gutterBottom>
                Upload Documents & Ask Questions
              </Typography>
              <Typography variant="body1" color="text.secondary" paragraph>
                Upload your documents and ask questions about their content.
                I'll use semantic search to find the most relevant information.
              </Typography>
              <Button
                variant="contained"
                startIcon={<AttachFileIcon />}
                onClick={() => fileInputRef.current.click()}
                sx={{
                  bgcolor: "#6e41e2",
                  "&:hover": { bgcolor: "#5a32c5" },
                }}
              >
                Upload a Document
              </Button>
            </Box>
          )}

          {/* Messages */}
          {messages.map((message, index) => (
            <Box
              key={index}
              sx={{
                display: "flex",
                mb: 2,
                maxWidth: "850px",
                alignSelf: message.type === "user" ? "flex-end" : "flex-start",
              }}
            >
              {message.type === "assistant" && (
                <Avatar sx={{ bgcolor: "#6e41e2", mr: 2 }}>
                  <SmartToyIcon />
                </Avatar>
              )}

              <Paper
                elevation={0}
                sx={{
                  p: 2,
                  borderRadius: 2,
                  maxWidth: "90%",
                  bgcolor: message.type === "user" ? "#e6f3ff" : "white",
                  border: message.error
                    ? "1px solid #f44336"
                    : "1px solid #e0e0e0",
                }}
              >
                {message.isFile ? (
                  <Box sx={{ display: "flex", alignItems: "center" }}>
                    <InsertDriveFileIcon sx={{ mr: 1 }} />
                    <Typography>{message.content}</Typography>
                  </Box>
                ) : (
                  <Typography sx={{ whiteSpace: "pre-wrap" }}>
                    {message.content}
                  </Typography>
                )}
              </Paper>

              {message.type === "user" && (
                <Avatar sx={{ bgcolor: "#1976d2", ml: 2 }}>
                  <PersonIcon />
                </Avatar>
              )}
            </Box>
          ))}

          {/* Auto-scroll anchor */}
          <div ref={messagesEndRef} />

          {/* Loading indicator */}
          {isLoading && (
            <Box sx={{ display: "flex", justifyContent: "center", my: 2 }}>
              <CircularProgress size={30} sx={{ color: "#6e41e2" }} />
            </Box>
          )}
        </Box>

        {/* Error message */}
        {error && (
          <Alert severity="error" onClose={() => setError("")} sx={{ m: 2 }}>
            {error}
          </Alert>
        )}

        {/* Input area */}
        <Paper
          component="form"
          onSubmit={handleSendMessage}
          sx={{
            p: 2,
            display: "flex",
            alignItems: "center",
            boxShadow: "0px -2px 10px rgba(0,0,0,0.05)",
            position: "relative",
            bgcolor: "white",
          }}
        >
          {/* File preview */}
          {file && (
            <Box
              sx={{
                position: "absolute",
                bottom: "100%",
                left: 0,
                right: 0,
                p: 1.5,
                bgcolor: "white",
                borderTop: "1px solid #e0e0e0",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center" }}>
                <InsertDriveFileIcon sx={{ mr: 1 }} />
                <Typography variant="body2" noWrap>
                  {file.name} ({(file.size / 1024).toFixed(1)} KB)
                </Typography>
              </Box>
              <IconButton size="small" onClick={clearFile}>
                <CloseIcon fontSize="small" />
              </IconButton>
            </Box>
          )}

          {/* File input (hidden) */}
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: "none" }}
            onChange={handleFileChange}
            accept=".pdf,.docx,.xlsx,.jpg,.jpeg,.png,.txt"
          />

          {/* File upload button */}
          <IconButton
            color="primary"
            onClick={() => fileInputRef.current.click()}
            disabled={isLoading}
          >
            <AttachFileIcon />
          </IconButton>

          {/* Message input */}
          <TextField
            fullWidth
            variant="outlined"
            placeholder={
              file
                ? "Press send to upload your file..."
                : "Ask a question about your documents..."
            }
            value={input}
            onChange={handleInputChange}
            disabled={isLoading || !!file}
            sx={{
              mx: 1,
              "& .MuiOutlinedInput-root": {
                borderRadius: "24px",
              },
            }}
          />

          {/* Send button */}
          <Button
            variant="contained"
            endIcon={<SendIcon />}
            disabled={isLoading || (!input.trim() && !file)}
            type="submit"
            sx={{
              borderRadius: "24px",
              bgcolor: "#6e41e2",
              "&:hover": {
                bgcolor: "#5a32c5",
              },
            }}
          >
            {file ? "Upload" : "Send"}
          </Button>
        </Paper>
      </Box>
    </Box>
  );
}

export default App;
