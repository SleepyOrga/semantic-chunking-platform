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

# Kết nối SageMaker Runtime
sm = boto3.client('sagemaker-runtime', region_name=REGION)

# Kết nối PostgreSQL
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD)
cursor = conn.cursor()

app = FastAPI()

# Models
class QueryRequest(BaseModel):
    query: str
    top_k_props: int = 20
    top_m_passages: int = 5
    final_n: int = 3

class PassageOut(BaseModel):
    passage_id: str
    text: str
    score: float

# Helpers
def get_embedding(text: str) -> List[float]:
    resp = sm.invoke_endpoint(
        EndpointName=EMBED_ENDPOINT,
        ContentType="application/json",
        Body=json.dumps({"inputs": [text]})
    )
    return json.loads(resp['Body'].read())['embeddings'][0]

def get_rerank_scores(query: str, passages: List[str]) -> List[float]:
    resp = sm.invoke_endpoint(
        EndpointName=RERANK_ENDPOINT,
        ContentType="application/json",
        Body=json.dumps({"query": query, "passages": passages})
    )
    return json.loads(resp['Body'].read())['scores']

# API Endpoint
@app.post("/rag", response_model=List[PassageOut])
def rag(query_req: QueryRequest):
    q = query_req.query
    q_emb = get_embedding(q)
    emb_str = ','.join(map(str, q_emb))

    # 1. Retrieve top-K propositions
    cursor.execute(f"""
        SELECT prop_id, passage_id, embedding <-> ARRAY[{emb_str}]::vector AS dist
        FROM propositions
        ORDER BY embedding <-> ARRAY[{emb_str}]::vector
        LIMIT {query_req.top_k_props};
    """)
    props = cursor.fetchall()
    if not props:
        raise HTTPException(status_code=404, detail="No propositions found")

    # 2. Map propositions → passages
    scores = {}
    for _, pid, dist in props:
        scores[pid] = scores.get(pid, 0) + 1.0 / (dist + 1e-5)

    # 3. Fetch top-M passages
    top_passages = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:query_req.top_m_passages]
    ids = [pid for pid, _ in top_passages]
    format_ids = ','.join(f"'{pid}'" for pid in ids)
    cursor.execute(f"SELECT passage_id, text FROM passages WHERE passage_id IN ({format_ids});")
    passages = cursor.fetchall()

    # 4. Rerank
    texts = [t for (_, t) in passages]
    rerank_scores = get_rerank_scores(q, texts)

    # 5. Return top-N after rerank
    ranked = sorted(zip(passages, rerank_scores), key=lambda x: x[1], reverse=True)[:query_req.final_n]
    return [
        PassageOut(passage_id=pid, text=txt, score=score)
        for ((pid, txt), score) in ranked
    ]
