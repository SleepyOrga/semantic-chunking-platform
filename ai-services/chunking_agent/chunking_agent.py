import re
import time
import json
import boto3
from typing import List, Dict, Any, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MarkdownSemanticChunker")

class EnhancedMarkdownSemanticChunker:
    def __init__(
        self, 
        max_chunk_size: int = 1500,
        min_chunk_size: int = 200,
        chunk_overlap: int = 100,
        max_processing_time: int = 30,
        use_llm: bool = True,
        # bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        llm_timeout: int = 15,
        max_llm_tokens: int = 100000,  # Maximum tokens for LLM call
        max_embedding_chunk_size: int = 512,  # Maximum size for RAG/embedding
        aws_region: Optional[str] = None
    ):
        """
        Initialize the enhanced Markdown semantic chunker.
        
        Args:
            max_chunk_size: Maximum size of each chunk in characters
            min_chunk_size: Minimum size for a standalone chunk
            chunk_overlap: Number of characters to overlap between chunks
            max_processing_time: Maximum allowed processing time in seconds
            use_llm: Whether to use LLM for semantic enhancement
            bedrock_model_id: Amazon Bedrock model ID
            llm_timeout: Timeout for LLM calls in seconds
            max_llm_tokens: Maximum tokens for LLM requests
            max_embedding_chunk_size: Maximum tokens for embedding/RAG chunks
            aws_region: AWS region for Bedrock
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_processing_time = max_processing_time
        self.use_llm = use_llm
        self.bedrock_model_id = bedrock_model_id
        self.llm_timeout = llm_timeout
        self.max_llm_tokens = max_llm_tokens
        self.max_embedding_chunk_size = max_embedding_chunk_size
        
        # Constants for token estimation
        self.chars_per_token = 4  # Rough estimate for token calculation
        
        # Common patterns for domain detection and tagging
        self.pattern_to_label = {
            r'(?i)customer|client|user|profile': 'Customer Info',
            r'(?i)loan|term|payment|interest|credit': 'Loan Terms',
            r'(?i)agreement|contract|terms|conditions|policy': 'Agreement',
            r'(?i)price|cost|fee|expense|budget|financial': 'Financial',
            r'(?i)procedure|process|step|workflow|instruction': 'Process',
            r'(?i)requirement|qualification|criteria|eligibility': 'Requirements',
            r'(?i)contact|email|phone|address|support': 'Contact Info',
            r'(?i)introduction|overview|summary|abstract': 'Introduction',
            r'(?i)conclusion|summary|results': 'Conclusion',
            r'(?i)appendix|reference|bibliography|glossary': 'Reference'
        }
        
        # Initialize Bedrock client if needed
        print(f"Initializing EnhancedMarkdownSemanticChunker with use_llm={use_llm}, aws_region={aws_region}")
        if use_llm:
            try:
                self.bedrock_client = boto3.client('bedrock-runtime', region_name=aws_region)
                logger.info("Successfully connected to Amazon Bedrock")
            except Exception as e:
                logger.warning(f"Could not connect to Amazon Bedrock: {e}")
                logger.info("Falling back to non-LLM processing")
                self.use_llm = False
    
    def extract_chunks(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract semantic chunks from a Markdown file.
        
        Args:
            file_path: Path to the Markdown file
            
        Returns:
            List of semantic chunks with metadata
        """
        start_time = time.time()
        logger.info(f"Processing file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return []
        
        # Step 1: Analyze document structure (fast)
        has_clear_structure = self._analyze_document_structure(content)
        logger.info(f"Document has clear structure: {has_clear_structure}")
        
        # Step 2: Initial structural chunking (fast)
        if has_clear_structure:
            chunks = self._chunk_by_headers(content)
            logger.info(f"Created {len(chunks)} header-based chunks")
        else:
            chunks = self._chunk_by_paragraphs(content)
            logger.info(f"Created {len(chunks)} paragraph-based chunks")
        
        # Step 3: Add basic tags (fast)
        chunks = self._add_basic_tags_to_chunks(chunks)
        
        # Step 4: Optimize chunks (fast)
        if len(chunks) > 100:
            chunks = self._optimize_chunks(chunks)
            logger.info(f"Optimized to {len(chunks)} chunks")
        
        # Store original document content for chunk reorganization
        self.original_document = content
        
        # Check remaining time
        time_spent = time.time() - start_time
        time_remaining = self.max_processing_time - time_spent
        logger.info(f"Initial processing completed in {time_spent:.2f}s")
        
        # Step 5: Use LLM to enhance and reorganize chunks if time permits
        print(f"Time remaining for LLM enhancement: {time_remaining:.2f}s")
        print(f"LLM timeout set to: {self.llm_timeout}s")
        if self.use_llm and time_remaining > self.llm_timeout:
            logger.info(f"Starting LLM enhancement with {time_remaining:.2f}s remaining")
            chunks = self._enhance_and_reorganize_chunks(chunks, time_remaining)
        
        # Step 6: Ensure all chunks are appropriate for embedding/RAG
        chunks = self._finalize_chunks_for_embedding(chunks)
        
        total_time = time.time() - start_time
        logger.info(f"Total processing completed in {total_time:.2f}s")
        logger.info(f"Generated {len(chunks)} semantic chunks")
        
        return chunks
    
    def _analyze_document_structure(self, content: str) -> bool:
        """
        Analyze document structure to determine best chunking strategy.
        
        Returns:
            Boolean indicating if document has clear header structure
        """
        # Count Markdown headers
        header_count = len(re.findall(r'(?:^|\n)#{1,6} ', content))
        
        # Count lines to estimate document size
        line_count = content.count('\n') + 1
        
        # Document has clear structure if it has enough headers relative to size
        return header_count >= min(5, line_count // 50)
    
    def _chunk_by_headers(self, content: str) -> List[Dict[str, Any]]:
        """
        Chunk document by Markdown headers.
        
        Args:
            content: Markdown content
            
        Returns:
            List of chunks based on header sections
        """
        chunks = []
        
        # Find all headers and corresponding content
        # Complex regex to capture headers and their content until the next header
        header_pattern = r'(?:^|\n)(#{1,6} .+?)(?=\n#{1,6} |\Z)'
        
        # Fall back to simpler pattern if the complex one doesn't match
        if not re.search(header_pattern, content, re.DOTALL):
            header_pattern = r'(?:^|\n)(#{1,6} .+)(?:\n|$)'
        
        matches = re.finditer(header_pattern, content, re.DOTALL)
        
        current_position = 0
        for match in matches:
            header_with_content = match.group(1)
            
            # Split header and content
            header_match = re.match(r'(#{1,6} .+)(?:\n|$)', header_with_content)
            
            if header_match:
                header = header_match.group(1).strip()
                # Content starts after header
                content_start = header_with_content.find('\n', len(header)) + 1
                section_content = header_with_content[content_start:].strip() if content_start > 0 else ""
                
                # Determine header level
                header_level = len(re.match(r'(#+)', header).group(1))
                header_text = header[header_level:].strip()
                
                # Store position in original document for potential reorganization
                start_pos = match.start()
                end_pos = match.end()
                
                # Check chunk size
                if len(section_content) > self.max_chunk_size:
                    # Split large content into smaller chunks
                    sub_chunks = self._split_large_content(section_content)
                    for i, sub_content in enumerate(sub_chunks):
                        chunks.append({
                            'title': f"{header_text} (part {i+1}/{len(sub_chunks)})",
                            'content': sub_content,
                            'header_level': header_level,
                            'original_title': header_text,
                            'start_pos': start_pos,
                            'end_pos': end_pos,
                            'is_subchunk': True,
                            'subchunk_index': i,
                            'total_subchunks': len(sub_chunks),
                            'token_count': self._estimate_tokens(sub_content)
                        })
                else:
                    chunks.append({
                        'title': header_text,
                        'content': section_content,
                        'header_level': header_level,
                        'original_title': header_text,
                        'start_pos': start_pos,
                        'end_pos': end_pos,
                        'is_subchunk': False,
                        'token_count': self._estimate_tokens(section_content)
                    })
            
            current_position = match.end()
        
        # Process remaining content if any
        if current_position < len(content):
            remaining = content[current_position:].strip()
            if remaining:
                chunks.append({
                    'title': 'Untitled Section',
                    'content': remaining,
                    'header_level': 0,
                    'original_title': None,
                    'start_pos': current_position,
                    'end_pos': len(content),
                    'is_subchunk': False,
                    'token_count': self._estimate_tokens(remaining)
                })
        
        return chunks
    
    def _chunk_by_paragraphs(self, content: str) -> List[Dict[str, Any]]:
        """
        Chunk document by paragraphs when no clear header structure exists.
        
        Args:
            content: Markdown content
            
        Returns:
            List of chunks based on paragraphs
        """
        chunks = []
        
        # Split by empty lines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', content)
        
        current_chunk = ""
        current_chunk_title = None
        start_pos = 0
        chunk_start_pos = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # Calculate position in original document
            para_start = content.find(para, start_pos)
            para_end = para_start + len(para)
            start_pos = para_end
            
            # Check if paragraph might be a title (not an official Markdown header)
            is_potential_title = (
                len(para) < 100 and 
                not para.startswith('- ') and 
                not para.startswith('* ') and 
                not para.startswith('```') and
                not para.startswith('|') and
                not re.match(r'^\d+\.', para)
            )
            
            # If this is a potential title and we already have content
            if is_potential_title and current_chunk:
                chunks.append({
                    'title': current_chunk_title or "Untitled Section",
                    'content': current_chunk,
                    'header_level': 0,
                    'original_title': current_chunk_title,
                    'start_pos': chunk_start_pos,
                    'end_pos': para_start,
                    'is_subchunk': False,
                    'token_count': self._estimate_tokens(current_chunk)
                })
                current_chunk = ""
                current_chunk_title = para
                chunk_start_pos = para_start
            
            # Add current paragraph to chunk
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
                
                # Set title if this could be a title
                if is_potential_title and not current_chunk_title:
                    current_chunk_title = para
                    current_chunk = ""  # Remove title from content
                    chunk_start_pos = para_start
            
            # Check chunk size
            if len(current_chunk) >= self.max_chunk_size:
                chunks.append({
                    'title': current_chunk_title or "Untitled Section",
                    'content': current_chunk,
                    'header_level': 0,
                    'original_title': current_chunk_title,
                    'start_pos': chunk_start_pos,
                    'end_pos': para_end,
                    'is_subchunk': False,
                    'token_count': self._estimate_tokens(current_chunk)
                })
                current_chunk = ""
                current_chunk_title = None
                chunk_start_pos = para_end
        
        # Add final chunk if any
        if current_chunk:
            chunks.append({
                'title': current_chunk_title or "Untitled Section",
                'content': current_chunk,
                'header_level': 0,
                'original_title': current_chunk_title,
                'start_pos': chunk_start_pos,
                'end_pos': len(content),
                'is_subchunk': False,
                'token_count': self._estimate_tokens(current_chunk)
            })
        
        return chunks
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for a text string.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        if not text:
            return 0
        # Simple estimation: ~4 characters per token for English text
        return len(text) // self.chars_per_token
    
    def _split_large_content(self, content: str) -> List[str]:
        """
        Split large content into smaller parts.
        
        Args:
            content: Content to split
            
        Returns:
            List of content parts
        """
        chunks = []
        
        # Split by paragraphs
        paragraphs = re.split(r'\n\s*\n', content)
        
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # Check if adding paragraph exceeds max size
            if len(current_chunk) + len(para) + 2 <= self.max_chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                # If current chunk is large enough, save it
                if current_chunk and len(current_chunk) >= self.min_chunk_size:
                    chunks.append(current_chunk)
                
                # Start new chunk
                current_chunk = para
                
                # Handle paragraph larger than max_chunk_size
                if len(para) > self.max_chunk_size:
                    # Split by sentences
                    sentences = re.split(r'(?<=[.!?])\s+', para)
                    
                    temp_chunk = ""
                    for sentence in sentences:
                        if len(temp_chunk) + len(sentence) + 1 <= self.max_chunk_size:
                            if temp_chunk:
                                temp_chunk += " " + sentence
                            else:
                                temp_chunk = sentence
                        else:
                            chunks.append(temp_chunk)
                            temp_chunk = sentence
                    
                    if temp_chunk:
                        current_chunk = temp_chunk
                    else:
                        current_chunk = ""
        
        # Add final chunk if any
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _add_basic_tags_to_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add basic tags to chunks using pattern matching.
        
        Args:
            chunks: List of chunks
            
        Returns:
            Chunks with added tags
        """
        for chunk in chunks:
            tags = []
            
            # Add tags based on title
            if chunk['title']:
                for pattern, label in self.pattern_to_label.items():
                    if re.search(pattern, chunk['title']):
                        tags.append(label)
            
            # Add tags based on content keywords
            for pattern, label in self.pattern_to_label.items():
                # Only scan first 500 chars for performance
                if re.search(pattern, chunk['content'][:500]) and label not in tags:
                    tags.append(label)
            
            # Add position-based tags if no other tags found
            if not tags:
                if chunk == chunks[0]:
                    tags.append('Introduction')
                elif chunk == chunks[-1]:
                    tags.append('Conclusion')
            
            chunk['tags'] = tags
        
        return chunks
    
    def _optimize_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Optimize chunks by merging small ones.
        
        Args:
            chunks: List of chunks
            
        Returns:
            Optimized list of chunks
        """
        if len(chunks) <= 1:
            return chunks
            
        result = []
        current_chunk = dict(chunks[0])
        
        for next_chunk in chunks[1:]:
            # Only merge if same header level or current chunk is small
            if (current_chunk['header_level'] == next_chunk['header_level'] and 
                len(current_chunk['content']) < self.min_chunk_size):
                
                combined_content = current_chunk['content'] + "\n\n" + next_chunk['content']
                
                if len(combined_content) <= self.max_chunk_size:
                    current_chunk['content'] = combined_content
                    # Update end position
                    current_chunk['end_pos'] = next_chunk['end_pos']
                    # Update token count
                    current_chunk['token_count'] = self._estimate_tokens(combined_content)
                    
                    # Merge tags
                    for tag in next_chunk['tags']:
                        if tag not in current_chunk['tags']:
                            current_chunk['tags'].append(tag)
                    continue
            
            # Add current chunk to result and start new chunk
            result.append(current_chunk)
            current_chunk = dict(next_chunk)
        
        # Add final chunk
        if current_chunk:
            result.append(current_chunk)
        
        return result
    
    def _calculate_max_batch_size(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Calculate the maximum number of chunks that can fit within token limits.
        
        Args:
            chunks: List of chunks to process
            
        Returns:
            Maximum number of chunks to process in one batch
        """
        # Base prompt overhead (estimated tokens)
        prompt_overhead = 800
        
        # Response overhead (tokens we reserve for LLM response)
        response_overhead = 4000
        
        # Available tokens for chunk content
        available_tokens = self.max_llm_tokens - prompt_overhead - response_overhead
        
        # Sort chunks by token count (ascending)
        sorted_chunks = sorted(chunks, key=lambda x: x.get('token_count', 0))
        
        # Calculate how many chunks we can include
        batch_size = 0
        total_tokens = 0
        
        # Additional tokens per chunk for context information
        per_chunk_overhead = 200
        
        for chunk in sorted_chunks:
            # Each chunk needs: content + title + overhead for formatting
            chunk_tokens = chunk.get('token_count', 0) + per_chunk_overhead
            
            if total_tokens + chunk_tokens <= available_tokens:
                batch_size += 1
                total_tokens += chunk_tokens
            else:
                break
        
        # Ensure we process at least one chunk
        return max(1, batch_size)
    
    def _enhance_and_reorganize_chunks(self, chunks: List[Dict[str, Any]], time_limit: float) -> List[Dict[str, Any]]:
        """
        Enhance chunks and reorganize them based on LLM suggestions.
        
        Args:
            chunks: List of chunks
            time_limit: Time limit in seconds
            
        Returns:
            Enhanced and reorganized chunks
        """
        start_time = time.time()
        
        try:
            # Dynamically determine how many chunks we can process
            max_batch_size = self._calculate_max_batch_size(chunks)
            logger.info(f"Calculated maximum batch size: {max_batch_size} chunks")
            
            # Prioritize chunks if there are too many
            if len(chunks) > max_batch_size:
                chunks_to_process = self._prioritize_chunks(chunks, max_batch_size)
                logger.info(f"Selected {len(chunks_to_process)}/{len(chunks)} priority chunks for LLM enhancement")
            else:
                chunks_to_process = chunks
                logger.info(f"Processing all {len(chunks)} chunks with LLM")
            
            # Create a batch prompt for all chunks including context
            prompt = self._create_reorganization_prompt(chunks_to_process)
            
            # Call LLM with batch prompt
            response = self.bedrock_client.invoke_model(
                modelId=self.bedrock_model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 4000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0
                })
            )
            
            # Process response
            response_body = json.loads(response['body'].read().decode('utf-8'))
            llm_response = response_body['content'][0]['text']
            
            # Parse batch response and reorganize chunks
            enhanced_chunks = self._parse_and_apply_reorganization(chunks, chunks_to_process, llm_response)
            
            time_spent = time.time() - start_time
            logger.info(f"LLM enhancement and reorganization completed in {time_spent:.2f}s")
            return enhanced_chunks
            
        except Exception as e:
            logger.error(f"Error in LLM processing: {e}")
            # Return original chunks if there's an error
            return chunks
    
    def _create_reorganization_prompt(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Create a prompt for enhancing and reorganizing chunks.
        
        Args:
            chunks: List of chunks to process
            
        Returns:
            Prompt for LLM
        """
        prompt = """You are a document analysis assistant specializing in semantic chunking.

        I'll provide you with multiple sections of a document that have been automatically chunked. Your task is to:

        1. Evaluate if each chunk represents a coherent semantic unit
        2. Suggest improvements for chunk boundaries (merge, split, or keep as is)
        3. Provide an improved title for each resulting chunk
        4. Generate 1-5 semantic tags for each resulting chunk

        For each chunk, determine if it:
        - Should be kept as is (if it forms a complete semantic unit)
        - Should be merged with adjacent chunks (if it's incomplete or too fragmented)
        - Should be split into smaller chunks (if it contains multiple distinct topics)

        I need your response in this JSON format:
        ```json
        {
          "reorganization": [
            {
              "action": "keep", 
              "chunk_ids": [0],
              "improved_title": "Better title here",
              "tags": ["tag1", "tag2", "tag3"],
              "reason": "This chunk forms a complete semantic unit."
            },
            {
              "action": "merge",
              "chunk_ids": [1, 2],
              "improved_title": "Combined title for merged chunks",
              "tags": ["tag1", "tag4", "tag5"],
              "reason": "These chunks are closely related and should be combined."
            },
            {
              "action": "split",
              "chunk_ids": [3],
              "split_points": ["First paragraph ends here.", "Second segment ends here."],
              "improved_titles": ["First part title", "Second part title", "Third part title"],
              "tags_for_parts": [["tag1", "tag2"], ["tag3", "tag4"], ["tag5", "tag6"]],
              "reason": "This chunk contains multiple distinct topics."
            }
          ]
        }
        Here are the document sections:

        """
        total_tokens = 0
          # Add each chunk to the prompt with context
        for i, chunk in enumerate(chunks):
            # For context, include information about adjacent chunks
            context = ""
            if i > 0:
                  prev_chunk = chunks[i-1]
                  context += f"Previous chunk title: {prev_chunk['title']}\n"
                  # Show truncated ending of previous chunk
                  prev_content_end = prev_chunk['content'][-100:].replace(chr(10), ' ')
                  context += f"Previous chunk ending: \"...{prev_content_end}\"\n\n"
              
            if i < len(chunks) - 1:
                  next_chunk = chunks[i+1]
                  context += f"Next chunk title: {next_chunk['title']}\n"
                  # Show truncated beginning of next chunk
                  next_content_start = next_chunk['content'][:100].replace(chr(10), ' ')
                  context += f"Next chunk beginning: \"{next_content_start}...\"\n\n"
              
              # Truncate content if too long for the prompt
            content = chunk['content']
            token_estimate = chunk.get('token_count', self._estimate_tokens(content))
            total_tokens += token_estimate

            # If content is very long, truncate for prompt but indicate this
            max_content_tokens = 1000  # Maximum tokens to include for a single chunk
            if token_estimate > max_content_tokens:
                  # Truncate content to fit within token limit
                  content_length = min(len(content), max_content_tokens * self.chars_per_token)
                  truncated_content = content[:content_length] + f"\n...[Content truncated, total length: {len(content)} chars]"
                  display_content = truncated_content
            else:
                  display_content = content
              
            prompt += f"""
              --- CHUNK {i} --- Title: {chunk['title']} Header level: {chunk['header_level']} Existing tags: {', '.join(chunk.get('tags', [])) or 'None'} Context: {context} Content: {display_content}

      """
            prompt += """Please analyze the semantic coherence of each chunk and suggest a reorganization plan in the JSON format described above. Focus on creating semantically complete units that make sense on their own. Consider both content and context when making your decisions. Only return the JSON, nothing else. """
            
        print(f"Total tokens in prompt: {total_tokens}")
        return prompt

    def _parse_and_apply_reorganization(self, all_chunks: List[Dict[str, Any]], 
                                      processed_chunks: List[Dict[str, Any]], 
                                      llm_response: str) -> List[Dict[str, Any]]:
        """
        Parse LLM response and apply chunk reorganization.
        
        Args:
            all_chunks: All original chunks
            processed_chunks: Chunks that were sent to LLM
            llm_response: Response from LLM
            
        Returns:
            Reorganized chunks
        """
        try:
            # Find and extract JSON from response
            json_match = re.search(r'```json\s*(.*?)\s*```', llm_response, re.DOTALL)
            if not json_match:
                json_match = re.search(r'({.*})', llm_response, re.DOTALL)
                
            if not json_match:
                logger.error("Could not find valid JSON in LLM response")
                return all_chunks
                
            reorganization_data = json.loads(json_match.group(1))
            
            if 'reorganization' not in reorganization_data:
                logger.error("LLM response missing 'reorganization' field")
                return all_chunks
            
            # Create a mapping of processed chunks for easier lookup
            processed_chunks_map = {i: chunk for i, chunk in enumerate(processed_chunks)}
            
            # Find the indices of processed chunks in all_chunks
            processed_indices = [all_chunks.index(chunk) for chunk in processed_chunks]
            
            # Create a new list for reorganized chunks
            reorganized_chunks = []
            
            # Track which chunks have been processed
            processed_chunk_ids = set()
            
            # Process each reorganization action
            for reorg_item in reorganization_data['reorganization']:
                action = reorg_item.get('action')
                chunk_ids = reorg_item.get('chunk_ids', [])
                
                # Skip if missing required fields
                if not action or not chunk_ids:
                    continue
                
                # Mark these chunks as processed
                processed_chunk_ids.update(chunk_ids)
                
                # Handle "keep" action
                if action == "keep" and len(chunk_ids) == 1:
                    chunk_id = chunk_ids[0]
                    if chunk_id in processed_chunks_map:
                        original_chunk = processed_chunks_map[chunk_id]
                        original_idx = processed_indices[chunk_id]
                        
                        # Create enhanced copy of the chunk
                        enhanced_chunk = dict(all_chunks[original_idx])
                        enhanced_chunk['title'] = reorg_item.get('improved_title', enhanced_chunk['title'])
                        enhanced_chunk['tags'] = reorg_item.get('tags', enhanced_chunk['tags'])
                        enhanced_chunk['llm_enhanced'] = True
                        enhanced_chunk['reorganization_reason'] = reorg_item.get('reason', "Kept as is")
                        
                        reorganized_chunks.append(enhanced_chunk)
                
                # Handle "merge" action
                elif action == "merge" and len(chunk_ids) > 1:
                    # Collect chunks to merge
                    chunks_to_merge = []
                    original_indices = []
                    
                    for chunk_id in chunk_ids:
                        if chunk_id in processed_chunks_map:
                            chunks_to_merge.append(processed_chunks_map[chunk_id])
                            original_indices.append(processed_indices[chunk_id])
                    
                    if chunks_to_merge:
                        # Create merged chunk
                        merged_content = "\n\n".join(chunk['content'] for chunk in chunks_to_merge)
                        merged_chunk = {
                            'title': reorg_item.get('improved_title', "Merged Section"),
                            'content': merged_content,
                            'header_level': min(chunk['header_level'] for chunk in chunks_to_merge),
                            'tags': reorg_item.get('tags', []),
                            'start_pos': min(chunk['start_pos'] for chunk in chunks_to_merge),
                            'end_pos': max(chunk['end_pos'] for chunk in chunks_to_merge),
                            'is_subchunk': False,
                            'llm_enhanced': True,
                            'merged_from': [all_chunks[idx]['title'] for idx in original_indices],
                            'reorganization_reason': reorg_item.get('reason', "Merged for semantic coherence"),
                            'token_count': self._estimate_tokens(merged_content)
                        }
                        
                        reorganized_chunks.append(merged_chunk)
                
                # Handle "split" action
                elif action == "split" and len(chunk_ids) == 1:
                    chunk_id = chunk_ids[0]
                    if chunk_id in processed_chunks_map:
                        original_chunk = processed_chunks_map[chunk_id]
                        original_idx = processed_indices[chunk_id]
                        original_content = original_chunk['content']
                        
                        # Get split points
                        split_points = reorg_item.get('split_points', [])
                        improved_titles = reorg_item.get('improved_titles', [])
                        tags_for_parts = reorg_item.get('tags_for_parts', [])
                        
                        # If valid split points provided
                        if split_points and len(improved_titles) == len(split_points) + 1:
                            # Create parts by finding split points in content
                            parts = []
                            last_pos = 0
                            
                            for split_point in split_points:
                                # Find position of split point in content
                                pos = original_content.find(split_point, last_pos)
                                if pos == -1:  # If split point not found
                                    continue
                                    
                                # Add end of split point to position
                                pos += len(split_point)
                                
                                # Extract part
                                part = original_content[last_pos:pos]
                                parts.append(part)
                                last_pos = pos
                            
                            # Add final part
                            if last_pos < len(original_content):
                                parts.append(original_content[last_pos:])
                            
                            # If splitting worked
                            if len(parts) > 1:
                                # Create new chunks for each part
                                for i, part in enumerate(parts):
                                    title = improved_titles[i] if i < len(improved_titles) else f"Split part {i+1}"
                                    tags = tags_for_parts[i] if i < len(tags_for_parts) else []
                                    
                                    split_chunk = {
                                        'title': title,
                                        'content': part,
                                        'header_level': original_chunk['header_level'],
                                        'tags': tags,
                                        'start_pos': original_chunk['start_pos'],  # Approximate
                                        'end_pos': original_chunk['end_pos'],      # Approximate
                                        'is_subchunk': True,
                                        'subchunk_index': i,
                                        'total_subchunks': len(parts),
                                        'llm_enhanced': True,
                                        'split_from': original_chunk['title'],
                                        'reorganization_reason': reorg_item.get('reason', "Split for semantic coherence"),
                                        'token_count': self._estimate_tokens(part)
                                    }
                                    
                                    reorganized_chunks.append(split_chunk)
                            else:
                                # If splitting failed, keep original
                                enhanced_chunk = dict(all_chunks[original_idx])
                                enhanced_chunk['llm_enhanced'] = True
                                enhanced_chunk['reorganization_reason'] = "Split failed, kept as is"
                                reorganized_chunks.append(enhanced_chunk)
                        else:
                            # If missing split details, keep original
                            enhanced_chunk = dict(all_chunks[original_idx])
                            enhanced_chunk['llm_enhanced'] = True
                            enhanced_chunk['reorganization_reason'] = "Invalid split points, kept as is"
                            reorganized_chunks.append(enhanced_chunk)
            
            # Add any chunks that weren't processed by the LLM
            for i, chunk in enumerate(processed_chunks):
                if i not in processed_chunk_ids:
                    # Find original index
                    original_idx = processed_indices[i]
                    reorganized_chunks.append(all_chunks[original_idx])
            
            # Add remaining chunks that weren't sent to the LLM
            for i, chunk in enumerate(all_chunks):
                if i not in processed_indices:
                    reorganized_chunks.append(chunk)
            
            # Sort chunks by their position in the original document
            reorganized_chunks.sort(key=lambda x: (x.get('start_pos', 0), x.get('end_pos', 0)))
            
            # Count enhanced chunks
            enhanced_count = sum(1 for chunk in reorganized_chunks if chunk.get('llm_enhanced', False))
            logger.info(f"Enhanced and reorganized {enhanced_count}/{len(reorganized_chunks)} chunks with LLM")
            
            return reorganized_chunks
            
        except Exception as e:
            logger.error(f"Error applying reorganization: {e}")
            # Return original chunks if error
            return all_chunks

    def _finalize_chunks_for_embedding(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ensure chunks are appropriate size for embedding/RAG.
        Split any chunks that are too large.
        
        Args:
            chunks: List of chunks
            
        Returns:
            List of embedding-appropriate chunks
        """
        embedding_chunks = []
        
        for chunk in chunks:
            # Check if chunk is too large for embedding
            token_count = chunk.get('token_count', self._estimate_tokens(chunk['content']))
            
            if token_count <= self.max_embedding_chunk_size:
                # Chunk is fine as is
                embedding_chunks.append(chunk)
            else:
                # Split chunk for embedding
                logger.info(f"Splitting chunk '{chunk['title']}' ({token_count} tokens) for embedding")
                
                # Create embedding-friendly chunks
                sub_chunks = self._create_embedding_chunks(chunk)
                
                # Add all sub-chunks
                embedding_chunks.extend(sub_chunks)
                
                logger.info(f"Split into {len(sub_chunks)} embedding-friendly chunks")
        
        # Update token counts
        for chunk in embedding_chunks:
            if 'token_count' not in chunk:
                chunk['token_count'] = self._estimate_tokens(chunk['content'])
        
        return embedding_chunks

    def _create_embedding_chunks(self, chunk: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split a large chunk into embedding-friendly sizes.
        
        Args:
            chunk: Large chunk to split
            
        Returns:
            List of smaller chunks suitable for embedding
        """
        content = chunk['content']
        max_chars = self.max_embedding_chunk_size * self.chars_per_token
        title = chunk['title']
        
        # Try to split on paragraph boundaries first
        paragraphs = re.split(r'\n\s*\n', content)
        
        sub_chunks = []
        current_chunk = ""
        part_index = 1
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # If adding paragraph would exceed limit
            if len(current_chunk) + len(para) + 2 > max_chars:
                # Save current chunk if not empty
                if current_chunk:
                    sub_chunks.append({
                        'title': f"{title} (part {part_index})",
                        'content': current_chunk,
                        'header_level': chunk.get('header_level', 0),
                        'tags': chunk.get('tags', []),
                        'start_pos': chunk.get('start_pos', 0),  # Approximate
                        'end_pos': chunk.get('end_pos', 0),      # Approximate
                        'is_subchunk': True,
                        'subchunk_index': part_index - 1,
                        'is_embedding_chunk': True,
                        'parent_chunk': title,
                        'token_count': self._estimate_tokens(current_chunk)
                    })
                    part_index += 1
                    current_chunk = para
                else:
                    # If a single paragraph is too large, need to split by sentences
                    if len(para) > max_chars:
                        # Split paragraph by sentences
                        sentences = re.split(r'(?<=[.!?])\s+', para)
                        sentence_chunks = self._split_into_chunks(sentences, max_chars)
                        
                        for i, sentence_chunk in enumerate(sentence_chunks):
                            sub_chunks.append({
                                'title': f"{title} (part {part_index})",
                                'content': sentence_chunk,
                                'header_level': chunk.get('header_level', 0),
                                'tags': chunk.get('tags', []),
                                'start_pos': chunk.get('start_pos', 0),  # Approximate
                                'end_pos': chunk.get('end_pos', 0),      # Approximate
                                'is_subchunk': True,
                                'subchunk_index': part_index - 1,
                                'is_embedding_chunk': True,
                                'parent_chunk': title,
                                'token_count': self._estimate_tokens(sentence_chunk)
                            })
                            part_index += 1
                    else:
                        current_chunk = para
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
        
        # Add final chunk if any
        if current_chunk:
            sub_chunks.append({
                'title': f"{title} (part {part_index})",
                'content': current_chunk,
                'header_level': chunk.get('header_level', 0),
                'tags': chunk.get('tags', []),
                'start_pos': chunk.get('start_pos', 0),  # Approximate
                'end_pos': chunk.get('end_pos', 0),      # Approximate
                'is_subchunk': True,
                'subchunk_index': part_index - 1,
                'is_embedding_chunk': True,
                'parent_chunk': title,
                'token_count': self._estimate_tokens(current_chunk)
            })
        
        return sub_chunks

    def _split_into_chunks(self, items: List[str], max_size: int) -> List[str]:
        """
        Split a list of items into chunks under max_size.
        
        Args:
            items: List of strings to chunk
            max_size: Maximum size per chunk
            
        Returns:
            List of combined strings within size limit
        """
        chunks = []
        current_chunk = ""
        
        for item in items:
            if len(current_chunk) + len(item) + 1 <= max_size:
                if current_chunk:
                    current_chunk += " " + item
                else:
                    current_chunk = item
            else:
                # Save current chunk
                if current_chunk:
                    chunks.append(current_chunk)
                
                # Start new chunk
                if len(item) <= max_size:
                    current_chunk = item
                else:
                    # If a single item is too large, truncate it
                    chunks.append(item[:max_size])
                    current_chunk = ""
        
        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks

    def _prioritize_chunks(self, chunks: List[Dict[str, Any]], sample_size: int) -> List[Dict[str, Any]]:
        """
        Prioritize chunks for LLM processing.
        
        Args:
            chunks: List of chunks
            sample_size: Number of chunks to select
            
        Returns:
            List of prioritized chunks
        """
        # Calculate score for each chunk
        chunk_scores = []
        for chunk in chunks:
            score = 0
            # Prioritize chunks with clear titles
            if chunk['title'] and chunk['title'] not in ["Untitled Section", "Phần không có tiêu đề"]:
                score += 10
            # Prioritize chunks with higher header levels
            score += (6 - min(chunk['header_level'], 5)) * 5 if chunk['header_level'] > 0 else 0
            # Prioritize chunks with optimal size
            content_len = len(chunk['content'])
            if 500 <= content_len <= 1500:
                score += 5
            elif content_len > 1500:
                score += 3  # Large chunks still useful but not optimal
            # Prioritize chunks with few or no tags
            if len(chunk.get('tags', [])) <= 1:
                score += 3
            # Prioritize subchunks (which might need better organization)
            if chunk.get('is_subchunk', False):
                score += 5
                
            chunk_scores.append((chunk, score))
        
        # Sort chunks by score (descending)
        chunk_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Get top N chunks
        return [chunk for chunk, score in chunk_scores[:sample_size]]

    def save_chunks(self, chunks: List[Dict[str, Any]], output_file: str = "markdown_chunks.json"):
        """
        Save chunks to JSON file.
        
        Args:
            chunks: List of chunks
            output_file: Output file path
        """
        try:
            # Clean chunks for serialization
            clean_chunks = []
            for chunk in chunks:
                clean_chunk = {k: v for k, v in chunk.items() if not k.startswith('_')}
                clean_chunks.append(clean_chunk)
                
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(clean_chunks, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(chunks)} chunks to {output_file}")
        except Exception as e:
            logger.error(f"Error saving chunks to file: {e}")
            
def process_markdown_file( file_path: str, output_file: Optional[str] = None, use_llm: bool = True, max_processing_time: int = 30, bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0", aws_region: Optional[str] = None ) -> List[Dict[str, Any]]: 
  """ Process a Markdown file to extract semantic chunks.
  Args:
      file_path: Path to Markdown file
      output_file: Path to save JSON output (optional)
      use_llm: Whether to use LLM enhancement
      max_processing_time: Maximum processing time in seconds
      bedrock_model_id: Amazon Bedrock model ID
      aws_region: AWS region for Bedrock
      
  Returns:
      List of semantic chunks
  """
  chunker = EnhancedMarkdownSemanticChunker(
      max_chunk_size=1500,
      min_chunk_size=200,
      chunk_overlap=100,
      max_processing_time=max_processing_time,
      use_llm=use_llm,
      bedrock_model_id=bedrock_model_id,
      aws_region=aws_region
  )

  chunks = chunker.extract_chunks(file_path)

  if output_file:
      chunker.save_chunks(chunks, output_file)

  return chunks


if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser(description="Extract semantic chunks from a Markdown file.")
  parser.add_argument("file_path", type=str, help="Path to the Markdown file")
  parser.add_argument("--output_file", type=str, default="markdown_chunks.json", help="Output JSON file path")
  parser.add_argument("--use_llm", action='store_true', help="Use LLM for chunk enhancement")
  parser.add_argument("--max_processing_time", type=int, default=30, help="Maximum processing time in seconds")
  parser.add_argument("--bedrock_model_id", type=str, default="anthropic.claude-3-sonnet-20240229-v1:0", help="Amazon Bedrock model ID")
  parser.add_argument("--aws_region", type=str, default=None, help="AWS region for Bedrock")
  start_time = time.time()
  args = parser.parse_args()

  chunks = process_markdown_file(
      args.file_path,
      output_file=args.output_file,
      use_llm=args.use_llm,
      max_processing_time=args.max_processing_time,
      bedrock_model_id=args.bedrock_model_id,
      aws_region=args.aws_region
  )

  end_time = time.time()
  print(f"Processing completed in {end_time - start_time:.2f} seconds.")
  print(f"Chunks saved to {args.output_file}")
  print(f"Total chunks created: {len(chunks)}")