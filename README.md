# 📄 Document Processing Platform

A scalable and modular platform for **document upload**, **semantic chunking**, **tagging**, and **search** using AI and event-driven architecture.

---

## 🏗️ Project Structure

This monorepo includes:

| Path                          | Description                                 |
|-------------------------------|---------------------------------------------|
| `frontend`                    | React + Material UI frontend UI             |
| `backend`                     | NestJS backend with S3, PostgreSQL, RabbitMQ|
| `ai-services/chunking_agent`  | Python agent for semantic chunking (LLM)    |
| `ai-services/tagging_agent`   | Python agent for tagging + proposition LLM  |

---

## ⚙️ Getting Started


### 1. Install dependencies

```bash
npm install
```

### 2. Prepare environment

- Add `semantic-chunking.pem` (AWS credential key) to project root
- Create `.env` file in `backend` with necessary keys

Example `.env`:

```bash
BACKEND_URL=http://localhost:4000
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-southeast-2
RABBITMQ_HOST=52.65.216.159
RABBITMQ_USER=admin
RABBITMQ_PASS=admin
```

---

## 🚀 Running the Platform

### 0. Build docker
```bash
docker compose up --build
```

### Step 1: Run Backend

```bash
cd backend
npm run db:migrate     # Run database migrations
npm start              # Start NestJS backend
```

### Step 2: Run Frontend

```bash
cd frontend
npm start              # Start React frontend
```

### Step 3: Run Chunking Worker

```bash
cd ai-services/chunking_agent
python chunking_worker.py
```

### Step 4: Run Tagging Agent

```bash
cd ai-services/tagging_agent
python main.py
```

### Step 5: Run Embedding Agent

```bash
cd ai-services/embedding_agent
python main.py
```

---

## 🧪 RabbitMQ Queue Dashboard

You can monitor all queues (input/output/embedding) via the RabbitMQ dashboard:

- 🌐 URL: http://52.65.216.159:15672/#/queues
- 🔑 Username: admin
- �� Password: admin

### pgadmin

http://localhost:5050/login?next=/

- 🔑 Username: admin@admin.com
- �� Password: admin
