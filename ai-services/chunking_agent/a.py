import re
import json
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
import logging
from chunking_agent import EnhancedMarkdownSemanticChunker

class ExcelAwareMarkdownChunker(EnhancedMarkdownSemanticChunker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Enhanced patterns for Excel-derived content
        self.excel_patterns = {
            # Table patterns
            r'^\|.*\|.*\|$': 'Table Data',
            r'^[\-\s\|:]+$': 'Table Separator',
            r'^\s*\d+\.\s*\|\s*': 'Numbered Table Row',
            
            # Financial/numerical patterns
            r'\$[\d,]+\.?\d*|\€[\d,]+\.?\d*|£[\d,]+\.?\d*': 'Financial Data',
            r'\b\d{1,3}(,\d{3})*(\.\d+)?\s*%': 'Percentage',
            r'\b\d{4}-\d{2}-\d{2}\b|\b\d{2}/\d{2}/\d{4}\b': 'Date',
            r'Q[1-4]\s*\d{4}|H[12]\s*\d{4}|FY\s*\d{4}': 'Period',
            
            # Spreadsheet-specific content
            r'(?i)sheet\s*\d+|tab\s*\d+|worksheet': 'Sheet Reference',
            r'(?i)total|subtotal|sum|average|count|max|min': 'Aggregation',
            r'(?i)formula|calculation|computed': 'Calculation',
            
            # Business/analytical patterns
            r'(?i)revenue|profit|loss|margin|roi|kpi': 'Business Metrics',
            r'(?i)quarter|monthly|annual|ytd|mtd|qoq|yoy': 'Time Analysis',
            r'(?i)region|territory|market|segment': 'Geographic/Segment',
            r'(?i)product|service|category|line': 'Product Analysis',
        }
        
        # Add Excel patterns to existing patterns
        self.pattern_to_label.update(self.excel_patterns)
        
        # Chunk relationship patterns for Excel data
        self.relationship_patterns = {
            'header_data': r'(?i)(header|title|name)\s*[:：]\s*(.+)',
            'metric_value': r'([^:：\n]+)\s*[:：]\s*([\d$€£%,.-]+)',
            'table_header': r'^\|\s*([^|]+)\s*\|',
            'summary_reference': r'(?i)(total|sum|average|count).*?(\d+)'
        }

    def _analyze_document_structure(self, content: str) -> bool:
        """Enhanced structure analysis for Excel-derived content."""
        # Original header-based analysis
        header_count = len(re.findall(r'(?:^|\n)#{1,6} ', content))
        line_count = content.count('\n') + 1
        
        # Check for table structures (Excel-specific)
        table_rows = len(re.findall(r'^\|.*\|.*\|$', content, re.MULTILINE))
        table_separators = len(re.findall(r'^[\-\s\|:]+$', content, re.MULTILINE))
        
        # Check for structured data patterns
        has_structured_data = (
            table_rows > 3 or  # Has table content
            len(re.findall(r'\$[\d,]+', content)) > 5 or  # Has financial data
            len(re.findall(r'\d+%', content)) > 3  # Has percentages
        )
        
        # Document has clear structure if headers OR structured data
        return (header_count >= min(5, line_count // 50)) or has_structured_data

    def _detect_table_structures(self, content: str) -> List[Dict[str, Any]]:
        """Detect and extract table structures from Excel-derived markdown."""
        tables = []
        lines = content.split('\n')
        
        current_table = []
        table_start = -1
        
        for i, line in enumerate(lines):
            # Check if line is part of a table
            if re.match(r'^\|.*\|.*\|$', line.strip()):
                if not current_table:
                    table_start = i
                current_table.append(line.strip())
            elif re.match(r'^[\-\s\|:]+$', line.strip()) and current_table:
                # Table separator - continue building table
                current_table.append(line.strip())
            else:
                # End of table
                if len(current_table) > 2:  # Must have header + separator + at least 1 row
                    tables.append({
                        'start_line': table_start,
                        'end_line': i - 1,
                        'content': '\n'.join(current_table),
                        'row_count': len([row for row in current_table if not re.match(r'^[\-\s\|:]+$', row)]),
                        'type': 'markdown_table'
                    })
                current_table = []
                table_start = -1
        
        # Handle table at end of content
        if len(current_table) > 2:
            tables.append({
                'start_line': table_start,
                'end_line': len(lines) - 1,
                'content': '\n'.join(current_table),
                'row_count': len([row for row in current_table if not re.match(r'^[\-\s\|:]+$', row)]),
                'type': 'markdown_table'
            })
        
        return tables

    def _extract_structured_data_chunks(self, content: str) -> List[Dict[str, Any]]:
        """Extract chunks specifically for structured data (tables, metrics, etc.)."""
        chunks = []
        
        # Detect tables
        tables = self._detect_table_structures(content)
        
        for table in tables:
            # Analyze table content
            table_content = table['content']
            
            # Extract table headers
            header_match = re.search(r'^\|(.+)\|$', table_content, re.MULTILINE)
            headers = []
            if header_match:
                headers = [h.strip() for h in header_match.group(1).split('|')]
            
            # Determine table type based on content
            table_type = self._classify_table_content(table_content, headers)
            
            # Create chunk for table
            chunk = {
                'title': f"{table_type} Table",
                'content': table_content,
                'type': 'structured_data',
                'subtype': 'table',
                'table_info': {
                    'headers': headers,
                    'row_count': table['row_count'],
                    'table_type': table_type
                },
                'start_line': table['start_line'],
                'end_line': table['end_line'],
                'token_count': self._estimate_tokens(table_content),
                'tags': ['Table Data', table_type]
            }
            
            chunks.append(chunk)
        
        return chunks

    def _classify_table_content(self, table_content: str, headers: List[str]) -> str:
        """Classify the type of table based on content and headers."""
        content_lower = table_content.lower()
        headers_str = ' '.join(headers).lower()
        
        # Financial data table
        if (re.search(r'\$[\d,]+|\€[\d,]+|£[\d,]+', table_content) or
            any(word in headers_str for word in ['revenue', 'profit', 'cost', 'price', 'budget'])):
            return 'Financial Data'
        
        # Performance metrics table
        if (re.search(r'\d+%', table_content) or
            any(word in headers_str for word in ['growth', 'rate', 'performance', 'kpi', 'metric'])):
            return 'Performance Metrics'
        
        # Regional/geographic data
        if any(word in headers_str for word in ['region', 'country', 'state', 'territory', 'market']):
            return 'Geographic Data'
        
        # Product data
        if any(word in headers_str for word in ['product', 'item', 'category', 'sku']):
            return 'Product Data'
        
        # Time series data
        if (re.search(r'Q[1-4]|month|year|\d{4}', table_content) or
            any(word in headers_str for word in ['quarter', 'monthly', 'annual', 'period'])):
            return 'Time Series Data'
        
        return 'Data Table'

    def _enhance_chunk_relationships(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance chunks with relationship information specific to Excel data."""
        
        # Find chunks that reference each other
        for i, chunk in enumerate(chunks):
            chunk['relationships'] = []
            
            # Look for summary relationships
            if 'total' in chunk['content'].lower() or 'sum' in chunk['content'].lower():
                # This might be a summary chunk - find related detail chunks
                for j, other_chunk in enumerate(chunks):
                    if i != j and self._chunks_are_related(chunk, other_chunk):
                        chunk['relationships'].append({
                            'type': 'summarizes',
                            'target_chunk_index': j,
                            'relationship': 'This chunk summarizes data from the related chunk'
                        })
            
            # Look for table-text relationships
            if chunk.get('type') == 'structured_data':
                # Find narrative chunks that might explain this table
                for j, other_chunk in enumerate(chunks):
                    if (i != j and other_chunk.get('type') != 'structured_data' and
                        self._table_has_narrative_explanation(chunk, other_chunk)):
                        chunk['relationships'].append({
                            'type': 'explained_by',
                            'target_chunk_index': j,
                            'relationship': 'This table is explained by the related text'
                        })
        
        return chunks

    def _chunks_are_related(self, chunk1: Dict[str, Any], chunk2: Dict[str, Any]) -> bool:
        """Determine if two chunks are semantically related."""
        # Check for common keywords
        content1_words = set(re.findall(r'\b\w+\b', chunk1['content'].lower()))
        content2_words = set(re.findall(r'\b\w+\b', chunk2['content'].lower()))
        
        # Check for significant word overlap
        common_words = content1_words.intersection(content2_words)
        significant_words = common_words - {'the', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        return len(significant_words) >= 3

    def _table_has_narrative_explanation(self, table_chunk: Dict[str, Any], text_chunk: Dict[str, Any]) -> bool:
        """Check if a text chunk explains a table chunk."""
        table_headers = table_chunk.get('table_info', {}).get('headers', [])
        text_content = text_chunk['content'].lower()
        
        # Check if text mentions table headers or table type
        header_mentions = sum(1 for header in table_headers if header.lower() in text_content)
        
        return header_mentions >= 2

    def _add_excel_specific_metadata(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add metadata specific to Excel-derived content."""
        
        for chunk in chunks:
            # Add data type classification
            chunk['data_types'] = self._classify_data_types(chunk['content'])
            
            # Add numerical summary if chunk contains numbers
            numerical_data = re.findall(r'[\d,]+\.?\d*', chunk['content'])
            if numerical_data:
                chunk['numerical_summary'] = {
                    'count': len(numerical_data),
                    'has_currency': bool(re.search(r'[\$€£]', chunk['content'])),
                    'has_percentages': bool(re.search(r'\d+%', chunk['content'])),
                    'has_dates': bool(re.search(r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}', chunk['content']))
                }
            
            # Add sheet context if available (from conversion metadata)
            sheet_ref = re.search(r'(?i)sheet\s*(\d+|[a-z]+)', chunk['content'])
            if sheet_ref:
                chunk['sheet_reference'] = sheet_ref.group(1)
        
        return chunks

    def _classify_data_types(self, content: str) -> List[str]:
        """Classify the types of data present in the content."""
        data_types = []
        
        if re.search(r'\$[\d,]+|\€[\d,]+|£[\d,]+', content):
            data_types.append('financial')
        
        if re.search(r'\d+%', content):
            data_types.append('percentage')
        
        if re.search(r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}', content):
            data_types.append('temporal')
        
        if re.search(r'^\|.*\|.*\|$', content, re.MULTILINE):
            data_types.append('tabular')
        
        if re.search(r'(?i)(total|sum|average|count|max|min)', content):
            data_types.append('aggregated')
        
        if not data_types:
            data_types.append('textual')
        
        return data_types

    def extract_chunks(self, file_path: str) -> List[Dict[str, Any]]:
        """Enhanced chunk extraction with Excel-specific processing."""
        start_time = time.time()
        logger.info(f"Processing Excel-derived file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return []
        
        # Step 1: Detect document structure (including Excel structures)
        has_clear_structure = self._analyze_document_structure(content)
        logger.info(f"Document has clear structure: {has_clear_structure}")
        
        # Step 2: Extract structured data chunks first (Excel-specific)
        structured_chunks = self._extract_structured_data_chunks(content)
        logger.info(f"Found {len(structured_chunks)} structured data chunks")
        
        # Step 3: Process remaining content with standard chunking
        if has_clear_structure:
            standard_chunks = self._chunk_by_headers(content)
        else:
            standard_chunks = self._chunk_by_paragraphs(content)
        
        # Step 4: Combine and deduplicate chunks
        all_chunks = self._merge_chunk_types(structured_chunks, standard_chunks)
        logger.info(f"Total chunks after merging: {len(all_chunks)}")
        
        # Step 5: Add Excel-specific tags and metadata
        all_chunks = self._add_basic_tags_to_chunks(all_chunks)
        all_chunks = self._add_excel_specific_metadata(all_chunks)
        
        # Step 6: Enhance chunk relationships
        all_chunks = self._enhance_chunk_relationships(all_chunks)
        
        # Step 7: Optimize chunks
        if len(all_chunks) > 100:
            all_chunks = self._optimize_chunks(all_chunks)
        
        # Step 8: LLM enhancement (existing logic)
        time_spent = time.time() - start_time
        time_remaining = self.max_processing_time - time_spent
        
        if self.use_llm and time_remaining > self.llm_timeout:
            logger.info(f"Starting LLM enhancement with {time_remaining:.2f}s remaining")
            all_chunks = self._enhance_and_reorganize_chunks(all_chunks, time_remaining)
        
        # Step 9: Finalize for embedding
        all_chunks = self._finalize_chunks_for_embedding(all_chunks)
        
        total_time = time.time() - start_time
        logger.info(f"Excel-aware processing completed in {total_time:.2f}s")
        logger.info(f"Generated {len(all_chunks)} semantic chunks")
        
        return all_chunks

    def _merge_chunk_types(self, structured_chunks: List[Dict[str, Any]], 
                          standard_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge structured and standard chunks, avoiding duplication."""
        
        # Create position ranges for structured chunks
        structured_ranges = []
        for chunk in structured_chunks:
            start_line = chunk.get('start_line', 0)
            end_line = chunk.get('end_line', 0)
            structured_ranges.append((start_line, end_line))
        
        # Filter standard chunks that don't overlap with structured chunks
        filtered_standard = []
        for chunk in standard_chunks:
            chunk_start = chunk.get('start_pos', 0)
            chunk_end = chunk.get('end_pos', 0)
            
            # Convert to approximate line numbers for comparison
            # This is rough but should work for deduplication
            overlaps = False
            for struct_start, struct_end in structured_ranges:
                if not (chunk_end < struct_start or chunk_start > struct_end):
                    overlaps = True
                    break
            
            if not overlaps:
                filtered_standard.append(chunk)
        
        # Combine all chunks and sort by position
        all_chunks = structured_chunks + filtered_standard
        all_chunks.sort(key=lambda x: (x.get('start_pos', 0), x.get('start_line', 0)))
        
        return all_chunks

    def _create_reorganization_prompt(self, chunks: List[Dict[str, Any]]) -> str:
        """Enhanced prompt that considers Excel-specific content types."""
        
        base_prompt = """You are a document analysis assistant specializing in semantic chunking of business documents, particularly those derived from Excel spreadsheets and structured data.

        I'll provide you with multiple sections that have been automatically chunked. These may include:
        - Tables with financial data, metrics, or structured information
        - Narrative text explaining the data
        - Summary sections with aggregated information
        - Headers and metadata

        Your task is to:
        1. Evaluate semantic coherence of each chunk
        2. Consider data relationships (tables vs. explanatory text)
        3. Ensure financial/numerical data stays together contextually
        4. Group related metrics and their explanations
        5. Maintain table integrity while improving narrative flow

        Special considerations for Excel-derived content:
        - Keep table headers with their data
        - Group related financial metrics
        - Maintain relationships between summary and detail data
        - Preserve numerical context and units

        For each chunk, determine if it should be kept, merged, or split, considering these data relationships.

        Response format (JSON only):
        ```json
        {
          "reorganization": [
            {
              "action": "keep|merge|split",
              "chunk_ids": [0],
              "improved_title": "Better title considering data type",
              "tags": ["Business Metrics", "Financial Data", "Q3 Performance"],
              "reason": "Explanation considering data relationships",
              "data_context": "Additional context about data type/relationships"
            }
          ]
        }
        Document sections: """
        # Add chunk information with enhanced context for Excel data
        for i, chunk in enumerate(chunks):
            chunk_info = f"""--- CHUNK {i} --- Title: {chunk['title']} Type: {chunk.get('type', 'text')} Data Types: {', '.join(chunk.get('data_types', []))} Tags: {', '.join(chunk.get('tags', []))} """
                    # Add table-specific information
            if chunk.get('type') == 'structured_data':
                table_info = chunk.get('table_info', {})
                chunk_info += f"Table Type: {table_info.get('table_type', 'Unknown')}\n"
                chunk_info += f"Headers: {', '.join(table_info.get('headers', []))}\n"
                chunk_info += f"Rows: {table_info.get('row_count', 0)}\n"
            
            # Add numerical summary if available
            if 'numerical_summary' in chunk:
                num_summary = chunk['numerical_summary']
                chunk_info += f"Contains: {num_summary['count']} numbers"
                if num_summary['has_currency']:
                    chunk_info += ", currency values"
                if num_summary['has_percentages']:
                    chunk_info += ", percentages"
                chunk_info += "\n"
            
            # Add relationships
            if chunk.get('relationships'):
                chunk_info += f"Relationships: {len(chunk['relationships'])} connections\n"
            
            chunk_info += f"Content: {chunk['content'][:800]}{'...' if len(chunk['content']) > 800 else ''}\n"
            
            base_prompt += chunk_info
        
        base_prompt += """Please analyze these chunks considering their data types and relationships. Focus on creating semantically complete units that preserve data integrity and business context."""
        return base_prompt
  
  