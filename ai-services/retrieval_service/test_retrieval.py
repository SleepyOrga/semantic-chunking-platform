import requests
import json
import argparse
from typing import List, Dict, Any, Optional

# API configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

def print_header(title: str, width: int = 60) -> None:
    """Print a formatted header"""
    print(f"\n{'='*width}")
    print(f"{title.upper()}".center(width))
    print(f"{'='*width}")

def test_health() -> Dict[str, Any]:
    """Test the health check endpoint"""
    print_header("Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health", headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        
        print(f"Status: {data['status']}")
        print(f"Message: {data['message']}")
        print(f"Chunks count: {data.get('chunks_count', 0)}")
        print(f"Documents count: {data.get('documents_count', 0)}")
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"Health check failed: {str(e)}")
        return {}

def test_retrieval(query: str, top_k: int = 20, final_n: int = 10,
                  use_hybrid: bool = True, use_tag_filtering: bool = True) -> List[Dict[str, Any]]:
    """Test the RAG retrieval endpoint"""
    print_header(f"Testing Query: '{query}'")
    
    payload = {
        "query": query,
        "top_k_chunks": top_k,
        "final_n": final_n,
        "use_hybrid": use_hybrid,
        "use_tag_filtering": use_tag_filtering
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/rag", 
            json=payload, 
            headers=HEADERS
        )
        response.raise_for_status()
        results = response.json()
        
        print(f"Found {len(results)} relevant chunks:")
        for i, chunk in enumerate(results, 1):
            print(f"\n--- Chunk {i} ---")
            print(f"Chunk ID: {chunk['chunk_id']}")
            print(f"Document ID: {chunk['document_id']}")
            print(f"Score: {chunk['score']:.4f}")
            if 'rerank_score' in chunk and chunk['rerank_score'] is not None:
                print(f"Rerank Score: {chunk['rerank_score']:.4f}")
            print(f"Content: {chunk['content'][:200]}...")
        
        return results
    except requests.exceptions.RequestException as e:
        print(f"Retrieval failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return []

def run_smoke_test():
    """Run a series of test cases"""
    # Test health check
    health = test_health()
    if not health or health.get('status') != 'healthy':
        print("Service is not healthy. Exiting tests.")
        return
    
    # Test queries with different configurations
    queries = [
        "What is VPBank?",
        "How to open a savings account?",
        "What are the loan requirements?",
    ]
    
    for query in queries:
        # Test with tag filtering
        print("\n" + "-"*60)
        print("WITH TAG FILTERING")
        print("-"*60)
        test_retrieval(query, use_tag_filtering=True)
        
        # Test without tag filtering
        print("\n" + "-"*60)
        print("WITHOUT TAG FILTERING")
        print("-"*60)
        test_retrieval(query, use_tag_filtering=False)

def main():
    parser = argparse.ArgumentParser(description="Test the Retrieval Service API")
    
    # Create subparsers for different test modes
    subparsers = parser.add_subparsers(dest='command', help='Test command to run')
    
    # Health check command
    health_parser = subparsers.add_parser('health', help='Run health check')
    
    # Single query command
    query_parser = subparsers.add_parser('query', help='Test a single query')
    query_parser.add_argument('query', type=str, help='The query to test')
    query_parser.add_argument('--top-k', type=int, default=5, help='Number of chunks to retrieve')
    query_parser.add_argument('--final-n', type=int, default=3, help='Number of final results to return')
    query_parser.add_argument('--no-hybrid', action='store_false', dest='use_hybrid', 
                            help='Disable hybrid search')
    query_parser.add_argument('--no-tag-filtering', action='store_false', dest='use_tag_filtering',
                            help='Disable tag filtering')
    
    # Smoke test command
    smoke_parser = subparsers.add_parser('smoke', help='Run smoke tests')
    
    args = parser.parse_args()
    
    if args.command == 'health':
        test_health()
    elif args.command == 'query':
        test_retrieval(
            query=args.query,
            top_k=args.top_k,
            final_n=args.final_n,
            use_hybrid=args.use_hybrid,
            use_tag_filtering=args.use_tag_filtering
        )
    elif args.command == 'smoke':
        run_smoke_test()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
