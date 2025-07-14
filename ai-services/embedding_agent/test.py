import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

# --- AWS Config ---
region = os.getenv("AWS_REGION", "us-east-1")
endpoint_name = os.getenv("EMBEDDING_ENDPOINT_NAME", "embedding-endpoint")  # thay bằng tên thực tế
aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

# --- SageMaker Runtime client ---
client = boto3.client(
    "sagemaker-runtime",
    region_name=region,
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
)

# --- Prepare mock data (batch) ---
mock_sentences = [
    "What is the capital of France?",
    "How does photosynthesis work?",
    "Explain the theory of relativity.",
    "Who wrote 'To Kill a Mockingbird'?",
    "What's the best way to learn Python?",
    "Summarize the causes of World War I.",
    "Describe the water cycle.",
    "How do I bake a chocolate cake?",
    "What is machine learning?",
    "Define quantum entanglement.",
]

# Format as JSON payload (match your model's expected input)
payload = json.dumps({
    "inputs": mock_sentences
})

# --- Invoke SageMaker Endpoint ---
response = client.invoke_endpoint(
    EndpointName=endpoint_name,
    ContentType="application/json",
    Body=payload
)

# --- Read and parse result ---
result = json.loads(response["Body"].read().decode("utf-8"))

# --- Print embeddings ---
for i, embedding in enumerate(result):
    print(f"[{i}] {mock_sentences[i]}")
    print(f"→ Embedding (length {len(embedding)}): {embedding[:5]}...\n")  # chỉ hiển thị 5 giá trị đầu
