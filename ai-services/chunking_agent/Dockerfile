FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY chunking.py .
COPY .env* ./

# Create non-root user
RUN useradd -m -u 1000 chunking && chown -R chunking:chunking /app
USER chunking

# Expose port (if needed for health checks)
EXPOSE 8000

# Use ENTRYPOINT to support command-line arguments
ENTRYPOINT ["python", "chunking.py"]
