# Document Processing Platform

A scalable platform for document upload, processing, and semantic search.

## Project Structure

This is a monorepo containing:
- `packages/frontend`: React + Material UI frontend
- `packages/backend`: NestJS backend with S3 integration

## Getting Started

1. Install dependencies:
```bash
npm install

2. Add semantic-chunking.pem to project root and .env to backend


3. Watch RabbitMQ on EC2
Access: http://<EC2_PUBLIC_IP>:15672
#http://54.92.209.245:15672 (development)
#http://52.65.216.159:15672 (production)

User/pass: admin / admin

