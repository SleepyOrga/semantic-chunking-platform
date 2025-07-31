# Retrieval Service API Documentation

This service provides a retrieval-augmented generation (RAG) API that allows you to search and retrieve relevant document chunks based on semantic similarity using vector embeddings.

## Table of Contents
- [Base URL](#base-url)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
  - [Health Check](#health-check)
  - [RAG Endpoint](#rag-endpoint)
- [Request/Response Examples](#requestresponse-examples)
- [Error Handling](#error-handling)
- [Configuration](#configuration)

## Base URL
```
http://localhost:8000  # Default local development
```

## Authentication
This API currently doesn't require authentication for local development. For production, consider adding API key authentication.

## API Endpoints

### Health Check
Check if the service is running.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "message": "Service is running",
  "timestamp": "2025-07-30T04:50:11.123456"
}
```

### RAG Endpoint
Retrieve relevant document chunks based on semantic similarity to the input query.

**Endpoint:** `POST /rag`

**Request Body:**
```typescript
{
  "query": string,               // Required: The search query
  "top_k_chunks": number,        // Optional: Number of chunks to retrieve (default: 10)
  "final_n": number,            // Optional: Number of final results to return (default: 5)
  "expand_query": boolean,      // Optional: Whether to expand the query using LLM (default: true)
  "use_hybrid": boolean,        // Optional: Whether to use hybrid search (default: true)
  "use_tag_filtering": boolean  // Optional: Whether to use tag filtering (default: true)
}
```

**Response:**
```typescript
[
  {
    "chunk_id": string,      // Unique identifier for the chunk
    "document_id": string,   // ID of the parent document
    "content": string,       // The actual text content of the chunk
    "score": number         // Similarity score (0-1)
  },
  ...
]
```

## Request/Response Examples

### Example 1: Basic Search
**Request:**
```bash
curl -X POST http://localhost:8000/rag \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the loan requirements?"}'
```

**Response:**
```json
[
  {
    "chunk_id": "7fab488d-edc6-4531-8d0b-a180522d6612",
    "document_id": "3d1643eb-0807-4de8-97b6-15d5553cabad",
    "content": "[1] Y. Bengio, P. Simard, and P. Frasconi. Learning long-term dependencies with gradient descent is difficult. IEEE Transactions on Neural Networks, 5(2):157-166, 1994.",
    "score": 0.92
  },
  ...
]
```

### Example 2: Advanced Search with Parameters
**Request:**
```bash
curl -X POST http://localhost:8000/rag \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to open a savings account?",
    "top_k_chunks": 15,
    "final_n": 3,
    "expand_query": true,
    "use_hybrid": true,
    "use_tag_filtering": true
  }'
```

## Error Handling

### Common HTTP Status Codes
- `200 OK`: Request was successful
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: No relevant chunks found
- `500 Internal Server Error`: Server error occurred

### Error Response Format
```json
{
  "detail": "Error message describing the issue"
}
```

## Configuration

### Environment Variables
```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password
DB_SSL=prefer

# Embedding Service
EMBED_ENDPOINT=embedding-endpoint
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

## Running the Service

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (copy from `.env.example` to `.env` and update values)

3. Start the server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The service will be available at `http://localhost:8000`

## Testing

Run the test suite:
```bash
python test_retrieval.py smoke
```

## API Documentation (Swagger UI)

For interactive API documentation and testing, visit:
```
http://localhost:8000/docs
```
