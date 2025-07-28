import requests
import json

# API endpoint
BASE_URL = "http://localhost:8000"

def test_rag_api():
    """Test the RAG API with sample queries"""
    
    test_queries = [
        "What is VPBank?",
        "What is method for law searching",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing query: {query}")
        print(f"{'='*60}")
        
        payload = {
            "query": query,
            "top_k_chunks": 10,
            "final_n": 3
        }
        
        try:
            response = requests.post(f"{BASE_URL}/rag", json=payload)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Found {len(data)} relevant chunks:")
                
                for i, chunk in enumerate(data, 1):
                    print(f"\n--- Chunk {i} ---")
                    print(f"Chunk ID: {chunk['chunk_id']}")
                    print(f"Document ID: {chunk['document_id']}")
                    print(f"Score: {chunk['score']:.4f}")
                    print(f"Content: {chunk['content'][:200]}...")
                    
            else:
                print(f"Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to API. Make sure the server is running.")
        except Exception as e:
            print(f"Error: {e}")

def test_simple_query():
    """Test with a single simple query"""
    payload = {
        "query": "What is VPBank?",
        "top_k_chunks": 5,
        "final_n": 2
    }
    
    try:
        response = requests.post(f"{BASE_URL}/rag", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Error: {e}")

def test_health_check():
    """Test the health endpoint to check database status"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health Check Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data['status']}")
            print(f"Message: {data['message']}")
            print(f"Chunks count: {data.get('chunks_count', 0)}")
            print(f"Documents count: {data.get('documents_count', 0)}")
        else:
            print(f"Health check failed: {response.text}")
            
    except Exception as e:
        print(f"Health check error: {e}")

def test_debug_documents():
    """Test the debug endpoint to check document statuses"""
    try:
        response = requests.get(f"{BASE_URL}/debug/documents")
        print(f"Debug Documents Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Document Status Counts:")
            for item in data.get('status_counts', []):
                print(f"  {item['status']}: {item['count']}")
            
            print("\nSample Documents:")
            for doc in data.get('sample_documents', [])[:5]:
                print(f"  ID: {doc['id']}, Status: {doc['status']}")
        else:
            print(f"Debug failed: {response.text}")
            
    except Exception as e:
        print(f"Debug error: {e}")

if __name__ == "__main__":
    print("Testing RAG API...")
    print("\n" + "="*60)
    print("HEALTH CHECK")
    print("="*60)
    test_health_check()
    
    print("\n" + "="*60)
    print("DEBUG DOCUMENTS")
    print("="*60)
    test_debug_documents()
    
    print("\n" + "="*60)
    print("SIMPLE QUERY TEST")
    print("="*60)
    test_simple_query()
    
    print("\n" + "="*80)
    test_rag_api()
