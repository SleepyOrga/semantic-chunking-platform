#!/bin/bash

# Script to start all parser workers

echo "🚀 Starting Parser Workers..."

# Set environment variables
export RABBITMQ_URL="amqp://admin:admin@52.65.216.159:5672/"
export AWS_REGION="ap-southeast-2"
export AWS_S3_BUCKET_NAME="semantic-chunking-bucket"

# Start DOCX Parser
echo "📄 Starting DOCX Parser..."
cd ai-services/xlsx_docx_parser
python docx_worker.py &
DOCX_PID=$!

# Start XLSX Parser
echo "📊 Starting XLSX Parser..."
python xlsx_worker.py &
XLSX_PID=$!

# Start PDF/OCR Parser
echo "📋 Starting PDF/OCR Parser..."
cd ../ocr_parser
python pdf_worker.py &
PDF_PID=$!

echo "✅ All parser workers started!"
echo "DOCX Parser PID: $DOCX_PID"
echo "XLSX Parser PID: $XLSX_PID"
echo "PDF Parser PID: $PDF_PID"

# Wait for any process to exit
wait

echo "🛑 Parser workers stopped."
