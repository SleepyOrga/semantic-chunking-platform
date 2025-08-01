// src/pages/HomePage.js
import React, { useState, useRef, useEffect } from "react";
import { Box, useMediaQuery } from "@mui/material";
import Header from "../components/Header/Header";
import Sidebar from "../components/Sidebar/SideBar";
import MessageList from "../components/Chat/MessageList";
import ChatInput from "../components/Chat/ChatInput";
import ErrorAlert from "../components/Common/ErrorAlert";
import DocumentViewer from "../components/Document/DocumentViewer";
import DocumentService from "../services/DocumentService";
import SearchService from "../services/SearchService";
import AuthService from "../services/AuthService";
import { useNavigate } from "react-router-dom";
import { flushSync } from "react-dom";

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

const HomePage = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [documentViewerOpen, setDocumentViewerOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const isMobile = useMediaQuery("(max-width:768px)");
  const navigate = useNavigate();

  // Check if user is authenticated
  useEffect(() => {
    if (!AuthService.isAuthenticated()) {
      navigate("/auth");
    } else {
      // Load user's documents
      loadUserDocuments();
    }
  }, [navigate]);

  // Load user documents
  const loadUserDocuments = async () => {
    try {
      setIsLoading(true);
      const data = await DocumentService.getUserDocuments();
      console.log("Loaded documents:", data);
      setUploadedFiles(data.documents || []);
    } catch (err) {
      setError("Failed to load documents. Please refresh the page.");
    } finally {
      setIsLoading(false);
    }
  };

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

  // Handle input change
  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  useEffect(() => {
    const checkRetrievalService = async () => {
      try {
        await SearchService.checkRetrievalServiceHealth();
        console.log("Retrieval service is available");
      } catch (err) {
        console.error("Retrieval service unavailable:", err);
        setError(
          "Search service is currently unavailable. Some features may be limited."
        );
      }
    };

    checkRetrievalService();
  }, []);

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

      const user = AuthService.getCurrentUser();
      const response = await DocumentService.uploadDocument(file, user.id);

      // Add uploaded file to list
      setUploadedFiles((prev) => [
        ...prev,
        {
          id: response.document_id,
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
      setError(err.message || "Error uploading file. Please try again.");

      // Add error message
      setMessages((prev) => [
        ...prev,
        {
          type: "assistant",
          content: `I couldn't process your file. ${
            err.message || "Please try again."
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
      await DocumentService.deleteDocument(fileId);

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

  // Handle viewing a document
  const handleViewDocument = (document) => {
    setSelectedDocument(document);
    setDocumentViewerOpen(true);
  };

  // Handle closing document viewer
  const handleCloseDocumentViewer = () => {
    setDocumentViewerOpen(false);
    setSelectedDocument(null);
  };

  // Handle sending a message/query
  // Update the handleSendMessage method in HomePage.js
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
      // Step 1: Retrieve chunks
      console.log("Retrieving chunks for query:", query);
      const chunks = await SearchService.getRelevantChunks(query, {
        topK: 20,
        finalN: 5,
        expandQuery: true,
        useHybrid: true,
      });
      console.log("Retrieved chunks:", chunks);

      if (!chunks || chunks.length === 0) {
        setMessages((prev) => [
          ...prev,
          {
            type: "assistant",
            content:
              "I couldn't find any relevant information to answer your question.",
            isFile: false,
          },
        ]);
        setIsLoading(false);
        return;
      }

      // Add interim message showing chunks were found
      const chunksSummary = SearchService.formatChunksSummary(chunks);
      setMessages((prev) => [
        ...prev,
        {
          type: "assistant",
          content: chunksSummary,
          isInterim: true,
          chunks: chunks,
        },
      ]);

      // Step 2: Start streaming the response

      // Add a placeholder message for the streaming content
      setMessages((prev) => [
        ...prev,
        {
          type: "assistant",
          content: "",
          isStreaming: true,
        },
      ]);

      try {
        let streamedResponse = "";
        let lastUpdateTime = Date.now();
        const UPDATE_THROTTLE_MS = 50;

        // Stream the response with error handling
        await SearchService.streamChatResponse(
          query,
          chunks,
          // On chunk received callback
          (textChunk) => {
            // Don't log the entire response each time
            console.log("Received chunk:", textChunk.substring(0, 20) + "...");

            // Append the new chunk
            streamedResponse += textChunk;

            const now = Date.now();
            if (now - lastUpdateTime > UPDATE_THROTTLE_MS) {
              lastUpdateTime = now;

              // Update the streaming message WITHOUT flushSync
              setMessages((prev) => {
                console.log("Updating messages state, throttled");
                const newMessages = [...prev];
                const streamingMsgIndex = newMessages.findIndex(
                  (m) => m.isStreaming
                );

                if (streamingMsgIndex !== -1) {
                  // Create a new object for React to detect the change
                  newMessages[streamingMsgIndex] = {
                    ...newMessages[streamingMsgIndex],
                    content: streamedResponse,
                  };
                }

                return newMessages;
              });
            } // Fixed: Properly close both flushSync and setMessages
          },
          // On error callback
          (errorMessage) => {
            console.error("Streaming error:", errorMessage);

            // Update the streaming message to show error
            setMessages((prev) => {
              const newMessages = [...prev];
              const streamingMsgIndex = newMessages.findIndex(
                (m) => m.isStreaming
              );

              if (streamingMsgIndex !== -1) {
                newMessages[streamingMsgIndex] = {
                  type: "assistant",
                  content:
                    streamedResponse ||
                    "I started generating a response but encountered an error.",
                  isError: true,
                  errorMessage:
                    errorMessage || "Error during response generation",
                  isStreaming: false,
                };
              }

              return newMessages;
            });
          }
        );

        // When streaming completes successfully, finalize the message
        setMessages((prev) => {
          const newMessages = [...prev];
          const streamingMsgIndex = newMessages.findIndex((m) => m.isStreaming);

          if (streamingMsgIndex !== -1) {
            newMessages[streamingMsgIndex] = {
              type: "assistant",
              content: streamedResponse,
              isFile: false,
              isStreaming: false,
            };
          }

          return newMessages;
        });
      } catch (streamingError) {
        console.error(
          "Streaming error caught in outer handler:",
          streamingError
        );
        // The error is already handled by the onError callback
        // No need to add another error message
      }
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

      // Safety check - make sure no messages are still marked as streaming
      setMessages((prev) =>
        prev.map((msg) =>
          msg.isStreaming ? { ...msg, isStreaming: false } : msg
        )
      );
    }
  };

  // Toggle sidebar
  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleFileButtonClick = () => {
    fileInputRef.current.click();
  };

  return (
    <Box
      sx={{
        height: "100vh",
        display: "flex",
        overflow: "hidden",
      }}
    >
      {/* Sidebar Component */}
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        isMobile={isMobile}
        files={uploadedFiles}
        onDeleteFile={handleDeleteFile}
        onUploadClick={handleFileButtonClick}
        onViewFile={handleViewDocument}
      />

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
        {/* Header Component */}
        <Header
          sidebarOpen={sidebarOpen}
          toggleSidebar={toggleSidebar}
          documentCount={uploadedFiles.length}
        />

        {/* MessageList Component */}
        <MessageList
          messages={messages}
          isLoading={isLoading}
          onUploadClick={handleFileButtonClick}
          messagesEndRef={messagesEndRef}
        />

        {/* Error Alert Component */}
        <ErrorAlert error={error} onClose={() => setError("")} />

        {/* ChatInput Component */}
        <ChatInput
          input={input}
          onInputChange={handleInputChange}
          onSubmit={handleSendMessage}
          file={file}
          onFileButtonClick={handleFileButtonClick}
          onClearFile={clearFile}
          isLoading={isLoading}
          fileInputRef={fileInputRef}
          onFileChange={handleFileChange}
        />
      </Box>

      {/* Document Viewer Dialog */}
      <DocumentViewer
        open={documentViewerOpen}
        onClose={handleCloseDocumentViewer}
        documentId={selectedDocument?.id}
        documentName={selectedDocument?.filename}
      />
    </Box>
  );
};

export default HomePage;
