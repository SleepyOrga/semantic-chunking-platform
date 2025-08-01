import json
import boto3
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import os
import logging
from chunking_agent import EnhancedMarkdownSemanticChunker
from model_manager import ModelManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BatchChunker:
    def __init__(self, max_workers: int = 6):
        self.max_workers = max_workers
        self.model_manager = ModelManager()
        self.s3 = boto3.client("s3", region_name="us-east-1")

    def process_single_document(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single document and return its chunks"""
        try:
            s3_bucket = job['s3Bucket']
            s3_key = job['s3Key']
            document_id = job['documentId']

            # Download file from S3
            with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as tmp_md:
                logger.info(f"Downloading {s3_key} from bucket {s3_bucket}")
                self.s3.download_fileobj(s3_bucket, s3_key, tmp_md)
                tmp_md_path = tmp_md.name

            # Initialize chunker with model from manager
            chunker = EnhancedMarkdownSemanticChunker(
                max_chunk_size=1500,
                min_chunk_size=200,
                chunk_overlap=100,
                max_processing_time=180,
                aws_region="us-east-1"  # Always use us-east-1 for Claude models
            )

            # Extract chunks
            chunks = chunker.extract_chunks(tmp_md_path)
            
            # Create output path
            output_json = f"{tmp_md_path}.chunks.json"
            
            # Save chunks locally
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(chunks, f, ensure_ascii=False, indent=2)

            # Upload to S3
            result_s3_key = s3_key.replace('.md', '.chunks.json')
            self.s3.upload_file(output_json, s3_bucket, result_s3_key)

            # Cleanup
            os.unlink(tmp_md_path)
            os.unlink(output_json)

            return {
                'document_id': document_id,
                'chunks': chunks,
                'status': 'success',
                'result_s3_key': result_s3_key
            }

        except Exception as e:
            logger.error(f"Error processing document {job.get('documentId')}: {str(e)}", exc_info=True)
            return {
                'document_id': job.get('documentId'),
                'status': 'error',
                'error': str(e)
            }

    def process_batch(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a batch of documents in parallel"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all jobs
            future_to_job = {
                executor.submit(self.process_single_document, job): job 
                for job in jobs
            }

            # Collect results as they complete
            for future in as_completed(future_to_job):
                job = future_to_job[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Job failed: {e}", exc_info=True)
                    results.append({
                        'document_id': job.get('documentId'),
                        'status': 'error',
                        'error': str(e)
                    })

        return results

if __name__ == "__main__":
    # Example usage
    test_jobs = [
        {
            's3Bucket': 'your-bucket',
            's3Key': 'doc1.md',
            'documentId': '1'
        },
        {
            's3Bucket': 'your-bucket',
            's3Key': 'doc2.md',
            'documentId': '2'
        }
    ]
    
    chunker = BatchChunker(max_workers=6)
    results = chunker.process_batch(test_jobs)
    print(json.dumps(results, indent=2))
