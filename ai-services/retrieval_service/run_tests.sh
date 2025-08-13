#!/bin/bash

# Set environment variables if needed
# export DB_HOST=localhost
# export DB_PORT=5432
# export DB_NAME=your_db
# export DB_USER=your_user
# export DB_PASSWORD=your_password

# Function to run the retrieval service in the background
start_service() {
    echo "🚀 Starting retrieval service..."
    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
    SERVICE_PID=$!
    
    # Wait for the service to start
    echo "⏳ Waiting for service to start..."
    until curl -s http://localhost:8000/health >/dev/null; do
        sleep 1
    done
    echo "✅ Service is running (PID: $SERVICE_PID)"
}

# Function to stop the service
stop_service() {
    if [ ! -z "$SERVICE_PID" ]; then
        echo "🛑 Stopping service (PID: $SERVICE_PID)..."
        kill $SERVICE_PID
    fi
}

# Handle script exit
trap stop_service EXIT

# Main script
case "$1" in
    start)
        start_service
        # Keep the script running
        wait $SERVICE_PID
        ;;
    test)
        start_service
        echo -e "\n🔍 Running tests..."
        python test_retrieval.py smoke
        ;;
    query)
        start_service
        shift
        echo -e "\n🔍 Running query: $@"
        python test_retrieval.py query "$@"
        ;;
    health)
        start_service
        python test_retrieval.py health
        ;;
    *)
        echo "Usage: $0 {start|test|query|health}"
        echo "  start   - Start the retrieval service"
        echo "  test    - Run smoke tests"
        echo "  query   - Run a test query (e.g., ./run_tests.sh query 'What is VPBank?')"
        echo "  health  - Check service health"
        exit 1
        ;;
esac
