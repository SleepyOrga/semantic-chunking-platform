# Embedding Agent

This service generates vector embeddings for text chunks using AWS SageMaker endpoints. It processes chunks from the chunking queue and stores embeddings in the database for similarity search and retrieval.

## 📋 Prerequisites

- AWS Account with SageMaker access
- HuggingFace API token
- RabbitMQ server running
- Backend API running

## 🚀 Quick Start

### 1. Environment Setup

Copy and configure your `.env` file:
```bash
cp .env.example .env
```

Required variables:
```properties
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# HuggingFace Token (for model access)
HUGGINGFACE_TOKEN=hf_your_token_here

# RabbitMQ Configuration
RABBITMQ_HOST=52.65.216.159
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASS=admin

# Backend API
BACKEND_URL=http://localhost:4000

# SageMaker Endpoint Name
SAGEMAKER_EMBEDDING_ENDPOINT=embedding-endpoint
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Deploy SageMaker Endpoint

**⚠️ WARNING: This creates billable AWS resources!**

```bash
python create_endpoints.py
```

This will:
- Deploy `intfloat/multilingual-e5-large-instruct` model
- Create endpoint named `embedding-endpoint`
- Use `ml.c5.2xlarge` instance (~$0.41/hour)

### 4. Run the Embedding Service

```bash
python main.py
```

The service will:
- Connect to RabbitMQ `embedding-input-queue`
- Process chunks in batches of 5
- Generate embeddings via SageMaker
- Update database via backend API

## 🛠️ Management Commands

### Endpoint Management

```bash
# List all endpoints
python manage_endpoints.py list

# Check endpoint status
python manage_endpoints.py status --endpoint embedding-endpoint

# Estimate costs
python manage_endpoints.py cost --endpoint embedding-endpoint

# Delete endpoint (with confirmation)
python manage_endpoints.py delete --endpoint embedding-endpoint

# Force delete (no confirmation)
python manage_endpoints.py delete --endpoint embedding-endpoint --force
```

### Direct Endpoint Deletion

```bash
# Interactive cleanup
python delete_endpoints.py

# Delete specific endpoint
python delete_endpoints.py embedding-endpoint
```

## 🧪 Testing

Test your SageMaker endpoint:
```bash
python test.py
```

This will send sample texts to the endpoint and show the generated embeddings.

## 📊 Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Chunking      │    │   Embedding      │    │   SageMaker     │
│   Service       │───▶│   Agent          │───▶│   Endpoint      │
│                 │    │   (Batch)        │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Backend API   │
                       │   (Database)    │
                       └─────────────────┘
```

### Message Flow

1. **Input**: Chunks from `embedding-input-queue`
   ```json
   {
     "id": 123,
     "type": "chunk",
     "content": "Text to embed..."
   }
   ```

2. **Processing**: 
   - Batch 5 messages together
   - Call SageMaker endpoint
   - Generate vector embeddings

3. **Output**: Update database via API
   - `PUT /chunks` for chunk embeddings
   - `PUT /chunk-components/{id}` for proposition embeddings

## ⚙️ Configuration

### Batch Processing
- `BATCH_SIZE = 5`: Messages per batch
- `BATCH_TIMEOUT = 1`: Seconds to wait for batch
- `MAX_CONCURRENT_BATCHES = 3`: Parallel requests

### SageMaker Model
- **Model**: `intfloat/multilingual-e5-large-instruct`
- **Instance**: `ml.c5.2xlarge` (CPU) or `ml.g5.xlarge` (GPU)
- **Pooling**: Mean pooling for embeddings

## 💰 Cost Management

### Hourly Costs (Approximate)
- `ml.c5.2xlarge`: ~$0.41/hour
- `ml.g5.xlarge`: ~$1.41/hour
- `ml.g5.2xlarge`: ~$2.27/hour

### Cost Optimization
1. **Stop endpoints** when not in use
2. **Use CPU instances** for batch processing
3. **Monitor usage** with CloudWatch
4. **Set up billing alerts**

```bash
# Check current costs
python manage_endpoints.py cost --endpoint embedding-endpoint

# Stop endpoint to save costs
python delete_endpoints.py embedding-endpoint
```

## 🔧 Troubleshooting

### Common Issues

1. **Endpoint doesn't exist**
   ```bash
   python manage_endpoints.py list
   python create_endpoints.py
   ```

2. **Authentication errors**
   - Check AWS credentials in `.env`
   - Verify IAM permissions for SageMaker

3. **Model loading timeout**
   - Large models take 5-10 minutes to load
   - Check endpoint status: `python manage_endpoints.py status -e embedding-endpoint`

4. **Queue connection failed**
   - Verify RabbitMQ is running
   - Check connection details in `.env`

### Logs and Monitoring

The service logs:
- Batch processing status
- SageMaker API calls
- Database updates
- Error messages

Monitor via:
- Console output
- AWS CloudWatch (SageMaker metrics)
- RabbitMQ management UI

## 🔄 Development

### Local Testing
```bash
# Test SageMaker endpoint
python test.py

# Send test message to queue
# (Use RabbitMQ management UI or backend API)
```

### Model Changes
To use a different embedding model:
1. Update `model_id` in `create_endpoints.py`
2. Redeploy endpoint: `python create_endpoints.py`
3. Update environment: `SAGEMAKER_EMBEDDING_ENDPOINT=new-endpoint-name`

## 📝 Notes

- **Embeddings are cached** in the database
- **Batch processing** improves throughput and reduces costs
- **Graceful shutdown** handles interruption during processing
- **Auto-retry** for failed SageMaker calls
- **Health checks** via endpoint status monitoring

Remember to **delete endpoints** when not in use to avoid unnecessary charges!
