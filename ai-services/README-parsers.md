# Independent Parser Services

This directory contains independent parser services for different file types (PDF, DOCX, XLSX) that run as separate processes and communicate via RabbitMQ.

## Architecture

- Each parser runs as an independent service
- RabbitMQ is used for message queuing between services
- The main application sends files to the appropriate parser queue based on file type
- Parsers process files and send results to a chunking queue

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements-parser.txt
   ```

2. Set up environment variables (or create a .env file):
   ```
   RABBITMQ_URL=amqp://username:password@host:port/
   S3_BUCKET_NAME=your-bucket-name
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   AWS_REGION=your-region
   ```

## Running the Services

### PDF Parser
```bash
python ocr_parser/main.py --rabbitmq amqp://admin:admin@52.65.216.159:5672
```

### DOCX Parser
```bash
python xlsx_docx_parser/parser_docx.py --rabbitmq amqp://admin:admin@52.65.216.159:5672
```

### XLSX Parser
```bash
python xlsx_docx_parser/parser_xlsx.py --rabbitmq amqp://admin:admin@52.65.216.159:5672
```

### Using the Generic Parser Worker
Alternatively, you can use the generic parser worker by specifying the parser type:

```bash
# For PDF files
python parser_worker.py --type pdf --rabbitmq amqp://admin:admin@52.65.216.159:5672

# For DOCX files
python parser_worker.py --type docx --rabbitmq amqp://admin:admin@52.65.216.159:5672

# For XLSX files
python parser_worker.py --type xlsx --rabbitmq amqp://admin:admin@52.65.216.159:5672
```

## Queue Structure

- `file-process-queue`: Main queue where files are initially sent
- `pdf-parser-queue`: Queue for PDF files
- `docx-parser-queue`: Queue for DOCX files
- `xlsx-parser-queue`: Queue for XLSX files
- `chunking-queue`: Queue where parsed content is sent for further processing

## Message Format

### File Processing Message
```json
{
  "s3Key": "path/to/file.pdf",
  "filename": "document.pdf",
  "documentId": "unique-document-id",
  "s3Bucket": "your-bucket-name"
}
```

### Chunking Queue Message
```json
{
  "s3Bucket": "your-bucket-name",
  "s3Key": "parsed/document-id/document.md",
  "documentId": "unique-document-id",
  "fileType": "pdf"
}
```

## Error Handling

- Failed messages are automatically sent to a dead letter queue
- Each parser has its own dead letter queue (e.g., `pdf-parser-queue.dlq`)
- Messages are retried up to 3 times before being sent to the DLQ

## Monitoring

- Use RabbitMQ management UI to monitor queue lengths and message processing
- Logs are written to stdout with timestamps and log levels
- Failed processing attempts are logged with stack traces for debugging
