from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Set, Union, AsyncGenerator
import boto3
import json
import psycopg2
import numpy as np
from dotenv import load_dotenv
import os
from datetime import datetime
import re
import asyncio

load_dotenv()

# Configuration
EMBED_ENDPOINT = os.getenv("EMBED_ENDPOINT", "embedding-endpoint")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
BEDROCK_MODEL_ID_2 = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-sonnet-20240229-v1:0")
BEDROCK_MODEL_ID_3 = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-sonnet-20240620-v1:0")

# Initialize Bedrock client
bedrock_client = boto3.client('bedrock-runtime', region_name=AWS_REGION)
REGION = os.getenv("AWS_REGION", "us-east-1")

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "your_db")
DB_USER = os.getenv("DB_USER", "your_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your_password")
DB_SSL = os.getenv("DB_SSL", "disable")

# Constants
DEFAULT_TOP_K = 50
DEFAULT_FINAL_N = 5

# Initialize SageMaker client
sm = boto3.client('sagemaker-runtime', region_name=REGION)

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        sslmode="require" if DB_SSL.lower() in ["enabled", "true", "require"] else "disable"
    )

conn = get_db_connection()
cursor = conn.cursor()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Hoặc ["*"] nếu muốn mở toàn bộ
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class QueryRequest(BaseModel):
    query: str
    top_k_chunks: int = DEFAULT_TOP_K
    final_n: int = DEFAULT_FINAL_N
    expand_query: bool = True
    use_hybrid: bool = True
    use_tag_filtering: bool = True

class ChunkOut(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    score: float
    rerank_score: Optional[float] = None

class HealthResponse(BaseModel):
    status: str
    message: str
    chunks_count: int = 0
    documents_count: int = 0

class ChatRequest(BaseModel):
    prompt: str
    chunks: List[ChunkOut]
    system_prompt: Optional[str] = None
    max_tokens: int = 2000
    temperature: float = 0.7

# Helper functions
def get_embedding(text: str) -> List[float]:
    resp = sm.invoke_endpoint(
        EndpointName=EMBED_ENDPOINT,
        ContentType="application/json",
        Body=json.dumps({"inputs": [text]})
    )
    response_body = json.loads(resp['Body'].read())
    # Handle different response formats
    if isinstance(response_body, list):
        return response_body[0]  # If response is directly a list of embeddings
    elif 'embeddings' in response_body:
        return response_body['embeddings'][0]  # If response has 'embeddings' key
    else:
        return response_body  # If response is the embedding itself

async def generate_related_tags(query: str, existing_tags: List[str]) -> List[str]:
    """Generate related tags for a query using AWS Bedrock LLM"""
    if not existing_tags:
        return []
        
    try:
        system_prompt = """You are a helpful assistant that identifies relevant tags for search queries.
        Your task is to select the most relevant tags from the provided list that match the given query.
        Return only a JSON array of the most relevant tags (up to 5) from the existing tags that best match the query.
        Only include tags that are relevant to the query.
        Example: ["tag1", "tag2", "tag3"]"""
        
        user_prompt = f"""Based on the following query, select the most relevant tags from the existing tags.
        
        Query: {query}
        
        Existing tags: {', '.join(existing_tags)}
        
        Return a JSON array of the most relevant tags (up to 5) from the existing tags that best match the query.
        Only include tags that are relevant to the query.
        
        Example: ["tag1", "tag2", "tag3"]"""
        
        # Call AWS Bedrock
        response = bedrock_client.invoke_model(
            modelId=BEDROCK_MODEL_ID_2,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 200,
                "temperature": 0.3,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            })
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read().decode('utf-8'))
        llm_output = response_body['content'][0]['text'].strip()
        
        # Try to extract JSON array from the output
        try:
            json_match = re.search(r'\[.*\]', llm_output, re.DOTALL)
            if json_match:
                tags = json.loads(json_match.group(0))
                if isinstance(tags, list) and all(isinstance(t, str) for t in tags):
                    # Filter to only include tags that exist in the database
                    valid_tags = [t for t in tags if t in existing_tags]
                    return valid_tags[:5]  # Return up to 5 matching tags
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"Error parsing tags from LLM response: {e}")
        
        return []
        
    except Exception as e:
        print(f"Error generating related tags: {e}")
        return []

async def get_rerank_scores(query: str, passages: List[str]) -> List[float]:
    """Get reranking scores for passages using AWS Bedrock"""
    try:
        if not passages:
            return []
            
        # Prepare the prompt for reranking
        system_prompt = """You are a helpful assistant that ranks text passages by their relevance to a query.
        Your task is to assign a relevance score between 0 and 1 to each passage, where 1 is most relevant.
        Return only a JSON array of scores in the same order as the passages, with no additional text."""
        
        # Format the passages for the prompt
        passages_text = ""
        for i, passage in enumerate(passages):
            passages_text += f"\n\n--- Passage {i+1} ---\n{passage}"
        
        user_prompt = f"""Query: {query}
        
        Please rank the following passages by their relevance to the query. 
        For each passage, provide a score between 0 and 1, where 1 is most relevant and 0 is not relevant at all.
        
        Return your response as a JSON array of scores in the same order as the passages.
        
        Passages to rank:{passages_text}"""
        
        # Call AWS Bedrock
        response = bedrock_client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "temperature": 0.1,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            })
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read().decode('utf-8'))
        llm_output = response_body['content'][0]['text'].strip()
        
        # Try to extract the scores from the LLM's response
        try:
            # Look for JSON array in the output
            json_match = re.search(r'\[.*\]', llm_output, re.DOTALL)
            if json_match:
                scores = json.loads(json_match.group(0))
                if isinstance(scores, list) and len(scores) == len(passages):
                    # Ensure all scores are floats between 0 and 1
                    scores = [max(0.0, min(1.0, float(score))) for score in scores]
                    return scores
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"Error parsing LLM response: {e}")
        
        # Fallback: If we couldn't parse scores, return equal scores
        print("Warning: Could not parse scores from LLM response, using fallback scoring")
        return [0.5] * len(passages)
        
    except Exception as e:
        print(f"Error in LLM reranking: {e}")
        # Return neutral scores if there's an error
        return [0.5] * len(passages) if passages else []
        return [0.0] * len(passages)

async def expand_query_with_llm(query: str, max_queries: int = 3) -> List[str]:
    """Generate multiple query variations using AWS Bedrock"""
    try:
        system_prompt = """You are a helpful assistant that generates search query variations.
        Your task is to create different search queries that would help find documents relevant to the user's original query.
        Return only a JSON array of search queries, with no additional text or explanation."""
        
        user_prompt = f"""Generate {max_queries} different search queries that would help find documents relevant to: "{query}"
        
        Return the queries as a JSON list of strings.
        Example: ["query 1", "query 2", "query 3"]"""
        
        # Call AWS Bedrock
        response = bedrock_client.invoke_model(
            modelId=BEDROCK_MODEL_ID_3,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 200,
                "temperature": 0.7,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            })
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read().decode('utf-8'))
        llm_output = response_body['content'][0]['text'].strip()
        
        # Try to extract JSON array from the output
        try:
            json_match = re.search(r'\[.*\]', llm_output, re.DOTALL)
            if json_match:
                queries = json.loads(json_match.group(0))
                if isinstance(queries, list) and all(isinstance(q, str) for q in queries):
                    # Remove duplicates while preserving order and limit to max_queries
                    return list(dict.fromkeys(queries))[:max_queries]
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"Error parsing queries from LLM response: {e}")
        
        # Fallback to original query if parsing fails
        return [query]
        
    except Exception as e:
        print(f"Error in query expansion: {e}")
        return [query]
        return [query]

async def hybrid_retrieval(query: str, query_embedding: List[float], top_k: int, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Perform vector similarity search with optional tag filtering"""
    emb_str = ','.join(map(str, query_embedding))
    
    try:
        # Build the base query with optional tag filtering
        where_clause = "WHERE 1=1"  # Always true condition
        params = []
        
        # Add tag filtering if tags are provided
        if tags and len(tags) > 0:
            where_clause += " AND c.tags && %s::text[]"
            params.append(tags)
        
        # Build the query with proper vector casting
        query = f"""
            SELECT 
                c.id, 
                c.document_id, 
                c.content,
                1.0 - (c.embedding <-> %s::vector) as score
            FROM chunks c
            {where_clause}
            ORDER BY c.embedding <-> %s::vector
            LIMIT %s;
        """
        
        # Convert embedding string to a proper array format for Postgres
        embedding_array = f"[{emb_str}]"
        
        # Add parameters to the query
        query_params = [embedding_array]  # First embedding param for the vector operation
        if tags and len(tags) > 0:
            query_params.append(tags)  # Add tags if they exist
        query_params.extend([embedding_array, top_k])  # Second embedding param and limit
        
        # Use a new cursor for this query to avoid transaction issues
        with conn.cursor() as cur:
            cur.execute(query, query_params)
            results = [
                {
                    'id': row[0],
                    'document_id': row[1],
                    'content': row[2],
                    'score': float(row[3])
                }
                for row in cur.fetchall()
            ]
        
        return results
        
    except Exception as e:
        print(f"Error in vector retrieval: {e}")
        return []

async def vector_search(embedding: List[float], top_k: int, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Perform vector similarity search with optional tag filtering"""
    try:
        # Start with base query
        query = """
            SELECT 
                c.id, 
                c.document_id, 
                c.content,
                1.0 - (c.embedding <-> ARRAY[%s]::vector) as score
            FROM chunks c
        """
        
        # Convert embedding to proper array format for Postgres
        embedding_array = f"[{','.join(map(str, embedding))}]"
        
        # Add tag filtering if tags are provided
        if tags and len(tags) > 0:
            query += """
                AND c.tags && %s::text[]
            """
            query_params = [
                embedding_array,  # First embedding param
                tags,            # Tags filter
                embedding_array,  # Second embedding param for ordering
                top_k            # Limit
            ]
        else:
            query_params = [
                embedding_array,  # First embedding param
                embedding_array,  # Second embedding param for ordering
                top_k            # Limit
            ]
        
        # Add ordering and limit
        query += """
            ORDER BY c.embedding <-> ARRAY[%s]::vector
            LIMIT %s;
        """
        
        # Use a new cursor for this query to avoid transaction issues
        with conn.cursor() as cur:
            cur.execute(query, query_params)
            results = [
                {
                    'id': row[0],
                    'document_id': row[1],
                    'content': row[2],
                    'score': float(row[3])
                }
                for row in cur.fetchall()
            ]
        
        return results
        
    except Exception as e:
        print(f"Error in vector search: {e}")
        return []

async def stream_bedrock_response(prompt: str, chunks: List[ChunkOut], system_prompt: Optional[str] = None, max_tokens: int = 2000, temperature: float = 0.7) -> AsyncGenerator[str, None]:
    """Stream response from Bedrock using chunks as context"""
    try:
        # Format chunks for context
        context = ""
        for i, chunk in enumerate(chunks):
            context += f"\n\nPASSAGE {i+1}:\n{chunk.content}"
        
        # Default system prompt if none provided
        if not system_prompt:
            system_prompt = """You are a helpful AI assistant that answers questions based on the provided document passages.
            When answering:
            - Rely primarily on the information in the provided passages
            - If the passages don't contain relevant information, say so politely
            - Do not make up information that isn't supported by the passages
            - Format your responses with markdown for readability
            - Cite specific passages when possible by referring to PASSAGE X
            """
        
        # Format user prompt with context
        user_prompt = f"""Here are some relevant passages from documents:

{context}

Based on these passages, please answer the following:

{prompt}"""

        # Create streaming request to Bedrock
        stream = bedrock_client.invoke_model_with_response_stream(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            })
        )
        
        # Process the streaming response
        async for event in stream.get_response_stream():
            if 'chunk' in event:
                chunk_data = json.loads(event['chunk']['bytes'])
                if 'content' in chunk_data and len(chunk_data['content']) > 0:
                    content_text = chunk_data['content'][0]['text']
                    yield content_text
                    
        # Send an empty string to signal the end of the stream
        yield ""
            
    except Exception as e:
        print(f"Error in streaming Bedrock response: {e}")
        yield f"\n\nI encountered an error while generating a response: {str(e)}"

# API Endpoints
@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint"""
    try:
        cursor.execute("SELECT COUNT(*) FROM chunks")
        chunks_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM documents")
        documents_count = cursor.fetchone()[0]
        
        return HealthResponse(
            status="healthy",
            message="Service is running",
            chunks_count=chunks_count,
            documents_count=documents_count
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            message=f"Database connection error: {str(e)}"
        )

@app.post("/rag", response_model=List[ChunkOut])
async def rag(query_req: QueryRequest):
    """Enhanced RAG endpoint with query expansion and hybrid search"""
    start_time = datetime.now()
    
    try:
        original_query = query_req.query
        queries = [original_query]
        print(f"[RAG] Processing query: '{original_query}'")
        print(f"[RAG] Settings: top_k={query_req.top_k_chunks}, final_n={query_req.final_n}, expand_query={query_req.expand_query}, use_hybrid={query_req.use_hybrid}, use_tag_filtering={query_req.use_tag_filtering}")
        
        # Query expansion - make async call
        if query_req.expand_query:
            print(f"[RAG] Expanding query: '{original_query}'")
            expanded_queries = await expand_query_with_llm(original_query)
            queries.extend(q for q in expanded_queries if q != original_query)
        
        all_results = []
        
        # Get all available tags for tag generation
        print("[RAG] Fetching existing tags for tag filtering")
        cursor.execute("""
            SELECT DISTINCT unnest(tags) as tag 
            FROM chunks 
            WHERE tags IS NOT NULL AND array_length(tags, 1) > 0;
        """)
        existing_tags = [row[0] for row in cursor.fetchall()] if cursor.rowcount > 0 else []
        
        # Generate related tags from the query - make async call
        print(f"[RAG] Generating related tags for query: '{original_query}'")
        related_tags = []
        if query_req.use_tag_filtering and existing_tags:
            related_tags = await generate_related_tags(original_query, existing_tags)
            print(f"Generated related tags: {related_tags}")
        
        print(f"[RAG] Processing {len(queries)} queries with related tags: {related_tags}")
        # Process each query
        for query in queries:
            try:
                # Get embedding for the query
                query_embedding = get_embedding(query)
                
                # Retrieve results based on search strategy
                if query_req.use_hybrid:
                    results = await hybrid_retrieval(query, query_embedding, query_req.top_k_chunks, 
                                                  related_tags if query_req.use_tag_filtering else None)
                else:
                    results = await vector_search(query_embedding, query_req.top_k_chunks, 
                                               related_tags if query_req.use_tag_filtering else None)
                
                all_results.extend(results)
            except Exception as e:
                print(f"Error processing query '{query}': {e}")
                continue
        
        if not all_results:
            raise HTTPException(status_code=404, detail="No relevant chunks found")
        
        # Deduplicate and sort results
        unique_results = {}
        for result in all_results:
            chunk_id = result['id']
            if chunk_id not in unique_results or result['score'] > unique_results[chunk_id]['score']:
                unique_results[chunk_id] = result
        
        top_results = sorted(
            unique_results.values(),
            key=lambda x: x['score'],
            reverse=True
        )[:query_req.top_k_chunks * 2]
        
        # Rerank with LLM - make async call
        passages = [r['content'] for r in top_results]
        rerank_scores = await get_rerank_scores(original_query, passages)
        
        # Combine scores
        final_results = []
        for idx, result in enumerate(top_results):
            rerank_score = float(rerank_scores[idx]) if idx < len(rerank_scores) else 0.0
            combined_score = (result['score'] * 0.3) + (rerank_score * 0.7)
            
            final_results.append({
                'id': result['id'],
                'document_id': result['document_id'],
                'content': result['content'],
                'score': combined_score,
                'rerank_score': rerank_score
            })
        
        # Sort by combined score and return top N
        final_results.sort(key=lambda x: x['score'], reverse=True)
        final_results = final_results[:query_req.final_n]
        
        print(f"Retrieval completed in {(datetime.now() - start_time).total_seconds():.2f}s")
        
        return [
            ChunkOut(
                chunk_id=r['id'],
                document_id=r['document_id'],
                content=r['content'],
                score=r['score'],
                rerank_score=r['rerank_score']
            )
            for r in final_results
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in RAG endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/stream")
async def stream_chat(chat_req: ChatRequest):
    """Stream a chat response based on user prompt and retrieved chunks"""
    try:
        # Validate input
        if not chat_req.prompt:
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")
        
        if not chat_req.chunks:
            raise HTTPException(status_code=400, detail="No context chunks provided")
        
        # Create a streaming response
        return StreamingResponse(
            stream_bedrock_response(
                chat_req.prompt, 
                chat_req.chunks,
                chat_req.system_prompt,
                chat_req.max_tokens,
                chat_req.temperature
            ),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        print(f"Error in chat stream endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)