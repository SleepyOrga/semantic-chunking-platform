import re


class ExcelPreprocessor:
    """Preprocessing steps specifically for Excel-derived markdown content"""
    
    def __init__(self):
        self.financial_patterns = r'(\$[\d,]+\.?\d*|\€[\d,]+\.?\d*|£[\d,]+\.?\d*)'
        self.percentage_patterns = r'(\d+\.?\d*%)'
        self.date_patterns = r'(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|Q[1-4]\s*\d{4})'
        
    def preprocess_excel_markdown(self, content: str) -> tuple[str, dict]:
        """
        Preprocessing steps for Excel-derived markdown
        
        Returns:
            (enhanced_content, metadata)
        """
        enhanced_content = content
        metadata = {
            'preprocessing_steps': [],
            'detected_patterns': {},
            'chunk_hints': {}
        }
        
        # Step 1: Enhance Table Context
        enhanced_content, table_metadata = self._enhance_table_context(enhanced_content)
        metadata['preprocessing_steps'].append('table_context_enhancement')
        metadata['detected_patterns'].update(table_metadata)
        
        # Step 2: Mark Financial Data Sections
        enhanced_content, financial_metadata = self._mark_financial_sections(enhanced_content)
        metadata['preprocessing_steps'].append('financial_section_marking')
        metadata['detected_patterns'].update(financial_metadata)
        
        # Step 3: Group Related Metrics
        enhanced_content, metrics_metadata = self._group_metrics(enhanced_content)
        metadata['preprocessing_steps'].append('metrics_grouping')
        metadata['detected_patterns'].update(metrics_metadata)
        
        # Step 4: Add Semantic Boundaries
        enhanced_content = self._add_excel_boundaries(enhanced_content)
        metadata['preprocessing_steps'].append('semantic_boundaries')
        
        # Step 5: Preserve Sheet Structure
        enhanced_content = self._preserve_sheet_structure(enhanced_content)
        metadata['preprocessing_steps'].append('sheet_structure_preservation')
        
        # Step 6: Add Cross-Reference Markers
        enhanced_content = self._mark_cross_references(enhanced_content)
        metadata['preprocessing_steps'].append('cross_reference_marking')
        
        return enhanced_content, metadata
    
    def _enhance_table_context(self, content: str) -> tuple[str, dict]:
        """Add context markers around tables for better chunking"""
        lines = content.split('\n')
        enhanced_lines = []
        table_count = 0
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Detect table start
            if re.match(r'^\|.*\|.*\|$', line):
                table_count += 1
                
                # Look for table title in previous 3 lines
                table_title = "Data Table"
                for j in range(max(0, i-3), i):
                    prev_line = lines[j].strip()
                    if prev_line and not re.match(r'^[\-\s\|:]+$', prev_line) and len(prev_line) < 100:
                        table_title = prev_line
                        break
                
                # Add table context marker
                enhanced_lines.append(f"<!-- TABLE_START: {table_title} -->")
                
                # Add table rows until table ends
                while i < len(lines) and (re.match(r'^\|.*\|.*\|$', lines[i].strip()) or 
                                        re.match(r'^[\-\s\|:]+$', lines[i].strip())):
                    enhanced_lines.append(lines[i])
                    i += 1
                
                enhanced_lines.append("<!-- TABLE_END -->")
                continue
            
            enhanced_lines.append(lines[i])
            i += 1
        
        return '\n'.join(enhanced_lines), {'tables_detected': table_count}
    
    def _mark_financial_sections(self, content: str) -> tuple[str, dict]:
        """Mark sections containing financial data"""
        financial_matches = len(re.findall(self.financial_patterns, content))
        
        if financial_matches >= 3:
            # Add financial context markers
            content = re.sub(
                r'(.*' + self.financial_patterns + r'.*)',
                r'<!-- FINANCIAL_DATA -->\1<!-- /FINANCIAL_DATA -->',
                content,
                flags=re.MULTILINE
            )
        
        return content, {'financial_data_points': financial_matches}
    
    def _group_metrics(self, content: str) -> tuple[str, dict]:
        """Group related business metrics together"""
        metrics_patterns = [
            r'(?i)(revenue|profit|margin|growth|performance|kpi)',
            r'(?i)(total|sum|average|count|max|min)',
            r'(?i)(quarter|monthly|annual|ytd|qoq|yoy)'
        ]
        
        metrics_count = 0
        for pattern in metrics_patterns:
            matches = re.findall(pattern, content)
            metrics_count += len(matches)
        
        if metrics_count >= 5:
            # Add metrics grouping markers
            content = re.sub(
                r'(?i)(.*(?:revenue|profit|margin|kpi|growth|performance).*)',
                r'<!-- METRICS_GROUP -->\1<!-- /METRICS_GROUP -->',
                content,
                flags=re.MULTILINE
            )
        
        return content, {'metrics_detected': metrics_count}
    
    def _add_excel_boundaries(self, content: str) -> str:
        """Add semantic boundaries for Excel-specific structures"""
        # Mark summary sections
        content = re.sub(
            r'(?i)(.*(?:summary|total|conclusion).*)',
            r'<!-- SUMMARY_SECTION -->\1<!-- /SUMMARY_SECTION -->',
            content,
            flags=re.MULTILINE
        )
        
        # Mark data sections vs narrative sections
        lines = content.split('\n')
        enhanced_lines = []
        in_data_section = False
        
        for line in lines:
            # Check if line has structured data
            has_data = (re.search(r'\|.*\|', line) or 
                       re.search(self.financial_patterns, line) or
                       re.search(self.percentage_patterns, line))
            
            if has_data and not in_data_section:
                enhanced_lines.append("<!-- DATA_SECTION_START -->")
                in_data_section = True
            elif not has_data and in_data_section and line.strip():
                enhanced_lines.append("<!-- DATA_SECTION_END -->")
                in_data_section = False
            
            enhanced_lines.append(line)
        
        if in_data_section:
            enhanced_lines.append("<!-- DATA_SECTION_END -->")
        
        return '\n'.join(enhanced_lines)
    
    def _preserve_sheet_structure(self, content: str) -> str:
        """Preserve Excel sheet structure in markdown"""
        # Mark sheet headers (typically H1 or H2)
        content = re.sub(
            r'^(#{1,2}\s+.+)$',
            r'<!-- SHEET_HEADER -->\1<!-- /SHEET_HEADER -->',
            content,
            flags=re.MULTILINE
        )
        
        return content
    
    def _mark_cross_references(self, content: str) -> str:
        """Mark potential cross-references between sections"""
        reference_patterns = [
            (r'(?i)(total.*?[\d$€£%,]+)', 'TOTAL_REFERENCE'),
            (r'(?i)(see.*?table|refer.*?table)', 'TABLE_REFERENCE'),
            (r'(?i)(above|below|previous|following)', 'POSITION_REFERENCE')
        ]
        
        for pattern, marker in reference_patterns:
            content = re.sub(
                pattern,
                rf'<!-- {marker} -->\1<!-- /{marker} -->',
                content
            )
        
        return content