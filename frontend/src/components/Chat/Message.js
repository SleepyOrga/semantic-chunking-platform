import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Paper,
  CircularProgress,
  Divider,
  Chip,
} from "@mui/material";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const Message = ({ message }) => {
  const isUser = message.type === "user";

  const [showInterimLoader, setShowInterimLoader] = useState(true);
  const [showStreamingLoader, setShowStreamingLoader] = useState(true);

  // Update loader states when message props change
  useEffect(() => {
    // Hide streaming loader when streaming is complete
    if (message.isStreaming === false) {
      setShowStreamingLoader(false);
      setShowInterimLoader(false);
      return;
    }

    // Optional: You could add a timeout to auto-hide loaders after a period

    if (message.isInterim) {
      const timer = setTimeout(() => {
        setShowInterimLoader(false);
      }, 10000); // Hide after 10 seconds if forgotten

      return () => clearTimeout(timer);
    }
  }, [message.isStreaming, message.isInterim]);

  // For interim messages (chunk summary with actual chunks displayed)
  if (message.isInterim && message.chunks) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "flex-start",
          mb: 3,
          width: "100%",
        }}
      >
        <Paper
          elevation={2}
          sx={{
            p: 2.5,
            maxWidth: "95%",
            background: "linear-gradient(145deg, #f8fcff 0%, #f0f7ff 100%)",
            borderRadius: "12px",
            width: "100%",
            border: "1px solid rgba(88, 167, 254, 0.1)",
            boxShadow: "0 6px 16px rgba(0,0,0,0.05)",
          }}
        >
          <Typography 
            variant="body1" 
            sx={{ 
              mb: 1.5, 
              fontWeight: 600,
              color: "#37474f",
              letterSpacing: "0.01em",
            }}
          >
            {message.content}
          </Typography>

          <Box 
            sx={{ 
              maxHeight: "300px", 
              overflowY: "auto", 
              mb: 2,
              scrollbarWidth: "thin",
              "&::-webkit-scrollbar": {
                width: "6px",
              },
              "&::-webkit-scrollbar-track": {
                background: "transparent",
              },
              "&::-webkit-scrollbar-thumb": {
                background: "rgba(0,0,0,0.1)",
                borderRadius: "10px",
              },
            }}
          >
            {message.chunks.map((chunk, index) => (
              <Box
                key={index}
                sx={{
                  mb: 2,
                  p: 1.5,
                  backgroundColor: "rgba(255,255,255,0.7)",
                  borderRadius: "8px",
                  border: "1px solid rgba(0,0,0,0.06)",
                  transition: "all 0.2s ease",
                  "&:hover": {
                    boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
                    transform: "translateY(-2px)",
                  },
                }}
              >
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    mb: 1,
                  }}
                >
                  <Chip
                    label={`Passage ${index + 1}`}
                    size="small"
                    sx={{
                      background: "linear-gradient(45deg, #7FE786, #58A7FE)",
                      color: "white",
                      fontWeight: 500,
                    }}
                  />
                  <Chip
                    label={`Score: ${Math.round(chunk.score * 100)}%`}
                    size="small"
                    sx={{
                      backgroundColor: chunk.score > 0.7 ? "rgba(127, 231, 134, 0.15)" : "rgba(0,0,0,0.05)",
                      color: chunk.score > 0.7 ? "#2e7d32" : "rgba(0,0,0,0.6)",
                      fontWeight: 500,
                    }}
                  />
                </Box>
                <Typography 
                  variant="body2"
                  sx={{
                    lineHeight: 1.6,
                    color: "rgba(0,0,0,0.75)",
                  }}
                >
                  {chunk.content}
                </Typography>
              </Box>
            ))}
          </Box>

          <Divider sx={{ my: 1.5 }} />

          {showInterimLoader && (
            <Box sx={{ display: "flex", alignItems: "center", mt: 1 }}>
              <CircularProgress size={16} sx={{ mr: 1 }} />
              <Typography variant="caption" color="text.secondary">
                Generating response based on these passages...
              </Typography>
            </Box>
          )}
        </Paper>
      </Box>
    );
  }

  // For streaming messages
  if (message.isStreaming) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: isUser ? "flex-end" : "flex-start",
          mb: 2,
        }}
      >
        <Paper
          elevation={1}
          sx={{
            p: 2,
            maxWidth: "80%",
            backgroundColor: isUser ? "#e3f2fd" : "#ffffff",
            borderRadius: 2,
          }}
        >
          {message.content ? (
            // Use a regular pre-formatted text display during streaming for better performance
            // Only use ReactMarkdown after streaming is complete
            <pre
              style={{
                whiteSpace: "pre-wrap",
                fontFamily: "inherit",
                margin: 0,
              }}
            >
              {message.content}
            </pre>
          ) : (
            <Typography variant="body2" color="text.secondary">
              Thinking...
            </Typography>
          )}

          {message.isError ? (
            <Box sx={{ mt: 1, color: "error.main" }}>
              <Typography variant="caption">
                {message.errorMessage ||
                  "Error generating response. Please try again."}
              </Typography>
            </Box>
          ) : (
            <Box sx={{ display: "flex", mt: message.content ? 1 : 0 }}>
              <CircularProgress size={12} sx={{ mr: 0.5 }} />
              <CircularProgress
                size={12}
                sx={{ mr: 0.5, animationDelay: "0.2s" }}
              />
              <CircularProgress size={12} sx={{ animationDelay: "0.4s" }} />
            </Box>
          )}
        </Paper>
      </Box>
    );
  }

  // Regular message (enhanced design)
  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        mb: 3,
        px: { xs: 1, sm: 2 },
        position: "relative",
      }}
    >
      <Paper
        elevation={0}
        sx={{
          p: { xs: 2, sm: 2.5 },
          maxWidth: { xs: "85%", md: "75%" },
          background: isUser 
            ? 'linear-gradient(135deg, #7FE786 0%, #58A7FE 100%)' 
            : 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)',
          color: isUser ? "white" : "inherit",
          borderRadius: '18px',
          borderTopRightRadius: isUser ? '4px' : '18px',
          borderTopLeftRadius: isUser ? '18px' : '4px',
          boxShadow: isUser 
            ? '0 8px 20px rgba(88, 167, 254, 0.15)' 
            : '0 8px 20px rgba(0,0,0,0.05)',
          border: isUser ? 'none' : '1px solid rgba(0,0,0,0.04)',
          position: 'relative',
          transition: 'all 0.3s ease',
          transform: 'scale(1)',
          '&:hover': {
            transform: 'scale(1.01)',
            boxShadow: isUser 
              ? '0 10px 25px rgba(88, 167, 254, 0.2)' 
              : '0 10px 25px rgba(0,0,0,0.07)',
          },
          ...(message.error && { 
            background: 'linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%)',
            color: "#d32f2f",
            borderRadius: '16px',
            boxShadow: '0 4px 15px rgba(211, 47, 47, 0.1)',
          }),
          '& code': {
            backgroundColor: isUser ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.04)',
            color: isUser ? '#ffffff' : 'inherit',
            padding: '2px 6px',
            borderRadius: '4px',
            fontFamily: "'Roboto Mono', monospace",
            fontSize: '0.9em',
          },
          '& pre': {
            backgroundColor: isUser ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.03)',
            borderRadius: '8px',
            padding: '12px',
            overflowX: 'auto',
            margin: '10px 0',
            border: isUser ? '1px solid rgba(255,255,255,0.1)' : '1px solid rgba(0,0,0,0.05)',
          },
          '& a': {
            color: isUser ? '#ffffff' : '#2196f3',
            textDecoration: 'underline',
            fontWeight: 500,
          },
          '& blockquote': {
            borderLeft: isUser ? '4px solid rgba(255,255,255,0.3)' : '4px solid rgba(0,0,0,0.1)',
            margin: '0 0 16px',
            padding: '0 16px',
          }
        }}
      >
        {message.isFile ? (
          <Box>
            <Typography variant="body1" sx={{ fontWeight: 500 }}>{message.content}</Typography>
            {message.file && (
              <Box 
                sx={{ 
                  mt: 1.5, 
                  display: 'flex',
                  alignItems: 'center',
                  p: 1,
                  borderRadius: '8px',
                  background: isUser ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.03)',
                  maxWidth: 'fit-content'
                }}
              >
                <Box 
                  component="span" 
                  sx={{ 
                    mr: 1, 
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 28,
                    height: 28,
                    borderRadius: '50%',
                    background: isUser ? 'rgba(255,255,255,0.2)' : 'rgba(88, 167, 254, 0.1)'
                  }}
                >
                  <Box component="span" sx={{ fontSize: '16px' }}>📄</Box>
                </Box>
                <Box>
                  <Typography 
                    variant="caption" 
                    sx={{ 
                      display: 'block',
                      fontWeight: 500,
                      color: isUser ? 'rgba(255,255,255,0.9)' : 'rgba(0,0,0,0.7)'
                    }}
                  >
                    {message.file.name}
                  </Typography>
                  <Typography 
                    variant="caption" 
                    sx={{ 
                      fontSize: '0.7rem',
                      color: isUser ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.5)'
                    }}
                  >
                    {(message.file.size / 1024).toFixed(1)} KB
                  </Typography>
                </Box>
              </Box>
            )}
          </Box>
        ) : (
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        )}
      </Paper>
    </Box>
  );
};

export default Message;
