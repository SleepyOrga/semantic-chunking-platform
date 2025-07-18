from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import boto3, json
import psycopg2
import numpy as np
from dotenv import load_dotenv
import os
load_dotenv()

# Cấu hình
EMBED_ENDPOINT = "embedding-endpoint"
RERANK_ENDPOINT = "reranker-endpoint"
REGION = os.getenv("AWS_REGION", "us-east-1")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "your_db")
DB_USER = os.getenv("DB_USER", "your_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your_password")
DB_SSL = os.getenv("DB_SSL", "disable")

# Kết nối SageMaker Runtime
sm = boto3.client('sagemaker-runtime', region_name=REGION)

# Kết nối PostgreSQL
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    sslmode="require" if DB_SSL.lower() in ["enabled", "true", "require"] else "disable")
cursor = conn.cursor()

app = FastAPI()

# Models
class QueryRequest(BaseModel):
    query: str
    top_k_chunks: int = 20
    final_n: int = 3

class ChunkOut(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    score: float

class HealthResponse(BaseModel):
    status: str
    message: str
    chunks_count: int = 0
    documents_count: int = 0

# Helpers
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

def get_rerank_scores(query: str, passages: List[str]) -> List[float]:
    resp = sm.invoke_endpoint(
        EndpointName=RERANK_ENDPOINT,
        ContentType="application/json",
        Body=json.dumps({"query": query, "texts": passages})
    )
    response_body = json.loads(resp['Body'].read())
    print(f"Reranker response: {response_body}")  # Debug print
    
    # Handle different response formats
    if isinstance(response_body, list):
        # If it's a list of dicts with score field
        if response_body and isinstance(response_body[0], dict):
            return [item.get('score', 0.0) for item in response_body]
        return response_body
    elif 'scores' in response_body:
        scores = response_body['scores']
        if isinstance(scores[0], dict):
            return [item.get('score', 0.0) for item in scores]
        return scores
    else:
        return response_body

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
def health_check():
    try:
        # Check chunks count
        cursor.execute("SELECT COUNT(*) FROM chunks")
        chunks_count = cursor.fetchone()[0]
        
        # Check documents count (all documents)
        cursor.execute("SELECT COUNT(*) FROM documents")
        total_docs = cursor.fetchone()[0]
        
        # Check completed documents count
        cursor.execute("SELECT COUNT(*) FROM documents WHERE status = 'completed'")
        completed_docs = cursor.fetchone()[0]
        
        return HealthResponse(
            status="healthy",
            message=f"Database connected. Found {chunks_count} chunks, {total_docs} total documents, {completed_docs} completed documents.",
            chunks_count=chunks_count,
            documents_count=completed_docs
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            message=f"Database error: {str(e)}"
        )

# Debug endpoint to check document statuses
@app.get("/debug/documents")
def debug_documents():
    try:
        cursor.execute("SELECT status, COUNT(*) FROM documents GROUP BY status")
        status_counts = cursor.fetchall()
        
        cursor.execute("SELECT id, status FROM documents LIMIT 10")
        sample_docs = cursor.fetchall()
        
        return {
            "status_counts": [{"status": status, "count": count} for status, count in status_counts],
            "sample_documents": [{"id": doc_id, "status": status} for doc_id, status in sample_docs]
        }
    except Exception as e:
        return {"error": str(e)}

# API Endpoint
@app.post("/rag", response_model=List[ChunkOut])
def rag(query_req: QueryRequest):
    try:
        q = query_req.query
        q_emb = get_embedding(q)
        emb_str = ','.join(map(str, q_emb))

        # First, try with completed documents only
        cursor.execute("SELECT COUNT(*) FROM chunks c JOIN documents d ON c.document_id = d.id WHERE d.status = 'completed'")
        completed_chunks = cursor.fetchone()[0]
        
        # If no completed documents, use all chunks
        if completed_chunks == 0:
            cursor.execute("SELECT COUNT(*) FROM chunks")
            total_chunks = cursor.fetchone()[0]
            print(f"No completed documents found, using all {total_chunks} chunks")
            cursor.execute(f"""
                SELECT c.id, c.document_id, c.content, c.embedding <-> ARRAY[{emb_str}]::vector AS dist
                FROM chunks c
                ORDER BY c.embedding <-> ARRAY[{emb_str}]::vector
                LIMIT {query_req.top_k_chunks};
            """)
        else:
            print(f"Using {completed_chunks} chunks from completed documents")
            cursor.execute(f"""
                SELECT c.id, c.document_id, c.content, c.embedding <-> ARRAY[{emb_str}]::vector AS dist
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
                WHERE d.status = 'completed'
                ORDER BY c.embedding <-> ARRAY[{emb_str}]::vector
                LIMIT {query_req.top_k_chunks};
            """)
            
        chunks = cursor.fetchall()
        print(f"Retrieved {len(chunks)} chunks")
        
        if not chunks:
            raise HTTPException(status_code=404, detail=f"No chunks found. Completed chunks: {completed_chunks}")

        # 2. Prepare chunks for reranking
        chunk_data = [(chunk_id, doc_id, content) for chunk_id, doc_id, content, _ in chunks]
        texts = [content for _, _, content, _ in chunks]
        
        # 3. Rerank
        rerank_scores = get_rerank_scores(q, texts)
        print(f"Rerank scores: {rerank_scores}")  # Debug print
        
        # Ensure scores are numbers
        numeric_scores = []
        for score in rerank_scores:
            if isinstance(score, (int, float)):
                numeric_scores.append(float(score))
            elif isinstance(score, dict) and 'score' in score:
                numeric_scores.append(float(score['score']))
            else:
                numeric_scores.append(0.0)

        # 4. Return top-N after rerank
        ranked = sorted(zip(chunk_data, numeric_scores), key=lambda x: x[1], reverse=True)[:query_req.final_n]
        return [
            ChunkOut(chunk_id=chunk_id, document_id=doc_id, content=content, score=score)
            for ((chunk_id, doc_id, content), score) in ranked
        ]
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in RAG endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
