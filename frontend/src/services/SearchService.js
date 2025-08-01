import axios from "axios";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:4000";
const RETRIEVAL_API_URL =
  process.env.REACT_APP_RETRIEVAL_API_URL || "http://localhost:8000";

class SearchService {
  // Step 1: Get chunks from retrieval service
  async getRelevantChunks(query, options = {}) {
    try {
      if (!query) {
        throw new Error("Query cannot be empty");
      }

      console.log("Calling retrieval service:", `${RETRIEVAL_API_URL}/rag`);
      console.log("With query:", query);

      const response = await axios.post(
        `${RETRIEVAL_API_URL}/rag`,
        {
          query,
          top_k_chunks: options.topK || 20,
          final_n: options.finalN || 5,
          expand_query: options.expandQuery !== false,
          use_hybrid: options.useHybrid !== false,
          use_tag_filtering: options.useTagFiltering !== false,
        },
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      console.log("Retrieval response:", response.data);
      return response.data;
    } catch (error) {
      console.error("Error fetching chunks:", error);

      // More detailed error logging
      if (error.response) {
        // Server responded with error status
        console.error(
          "Response error:",
          error.response.status,
          error.response.data
        );
      } else if (error.request) {
        // Request was made but no response
        console.error("No response received:", error.request);
      } else {
        // Error in request setup
        console.error("Request setup error:", error.message);
      }

      throw error.response?.data || { message: "Failed to retrieve chunks" };
    }
  }

  // Step 2: Stream chat response using retrieved chunks
  // Add this to your streamChatResponse method

async streamChatResponse(userPrompt, chunks, onChunkReceived, onError) {
  try {
    console.log('Starting streaming chat with chunks:', chunks.length);
    
    const response = await fetch(`${RETRIEVAL_API_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        prompt: userPrompt,
        chunks: chunks,
        temperature: 0.7,
        max_tokens: 2000
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    console.log('Streaming response started');
    console.log('Stream response status:', response.status);
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    
    // Read the stream
    try {
      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          console.log('Stream reading completed');
          break;
        }
        
        // Decode the chunk and add to buffer
        const chunk = decoder.decode(value);
        buffer += chunk;
        
        // Process complete SSE messages from buffer
        const messages = buffer.split('\n\n');
        // Last part might be incomplete, keep it in buffer
        buffer = messages.pop() || '';
        
        for (const message of messages) {
          if (!message.trim()) continue;
          
          // Parse the SSE format
          if (message.startsWith('data: ')) {
            // Extract content after "data: "
            const content = message.substring(6);
            
            // Skip the [DONE] marker
            if (content === '[DONE]') {
              console.log('Stream complete marker received');
              continue;
            }
            
            // Pass the actual content (not the raw SSE message) to the callback
            console.log('Received chunk in search service:', content);
            onChunkReceived(content);
          }
        }
      }
    } catch (streamError) {
      console.error('Stream reading error:', streamError);
      if (onError) onError(streamError.message);
    }
  } catch (error) {
    console.error('Error in streaming chat response:', error);
    if (onError) onError(error.message);
    throw error;
  }
}

  // Format chunks summary for display
  formatChunksSummary(chunks) {
    if (!chunks || chunks.length === 0) {
      return "No relevant information found.";
    }

    const uniqueDocIds = new Set(chunks.map((chunk) => chunk.document_id));

    return `Found ${chunks.length} relevant passages from ${uniqueDocIds.size} document(s). Generating response...`;
  }

  // Health check for retrieval service
  async checkRetrievalServiceHealth() {
    try {
      const response = await axios.get(`${RETRIEVAL_API_URL}/health`);
      return response.data;
    } catch (error) {
      console.error("Health check failed:", error);
      throw error;
    }
  }
}

export default new SearchService();
