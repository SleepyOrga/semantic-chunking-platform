class WordPreprocessor:
    """Preprocessing steps for Word-derived markdown content"""
    
    def preprocess_word_markdown(self, content: str) -> tuple[str, dict]:
        """
        Preprocessing steps for Word-derived markdown
        """
        enhanced_content = content
        metadata = {
            'preprocessing_steps': [],
            'detected_patterns': {}
        }
        
        # Step 1: Preserve heading hierarchy
        enhanced_content = self._preserve_heading_hierarchy(enhanced_content)
        metadata['preprocessing_steps'].append('heading_hierarchy_preservation')
        
        # Step 2: Handle lists and bullet points
        enhanced_content = self._handle_lists(enhanced_content)
        metadata['preprocessing_steps'].append('list_handling')
        
        # Step 3: Preserve formatting context
        enhanced_content = self._preserve_formatting_context(enhanced_content)
        metadata['preprocessing_steps'].append('formatting_preservation')
        
        # Step 4: Handle embedded tables
        enhanced_content = self._handle_embedded_tables(enhanced_content)
        metadata['preprocessing_steps'].append('table_handling')
        
        # Step 5: Mark document sections
        enhanced_content = self._mark_document_sections(enhanced_content)
        metadata['preprocessing_steps'].append('section_marking')
        
        return enhanced_content, metadata
    
    def _preserve_heading_hierarchy(self, content: str) -> str:
        """Ensure heading hierarchy is properly maintained"""
        lines = content.split('\n')
        enhanced_lines = []
        
        for line in lines:
            # If it's a heading, add context marker
            if re.match(r'^#{1,6}\s+', line):
                level = len(re.match(r'^(#+)', line).group(1))
                enhanced_lines.append(f"<!-- HEADING_LEVEL_{level} -->")
                enhanced_lines.append(line)
                enhanced_lines.append(f"<!-- /HEADING_LEVEL_{level} -->")
            else:
                enhanced_lines.append(line)
        
        return '\n'.join(enhanced_lines)
    
    def _handle_lists(self, content: str) -> str:
        """Improve list handling for better chunking"""
        # Mark list sections
        lines = content.split('\n')
        enhanced_lines = []
        in_list = False
        
        for line in lines:
            if re.match(r'^\s*[-*+]\s+|^\s*\d+\.\s+', line):
                if not in_list:
                    enhanced_lines.append("<!-- LIST_START -->")
                    in_list = True
                enhanced_lines.append(line)
            else:
                if in_list and line.strip():
                    enhanced_lines.append("<!-- LIST_END -->")
                    in_list = False
                enhanced_lines.append(line)
        
        if in_list:
            enhanced_lines.append("<!-- LIST_END -->")
        
        return '\n'.join(enhanced_lines)
    
    def _preserve_formatting_context(self, content: str) -> str:
        """Preserve important formatting context"""
        # Mark bold/italic sections that might be important
        content = re.sub(
            r'\*\*(.*?)\*\*',
            r'<!-- BOLD -->\1<!-- /BOLD -->',
            content
        )
        
        content = re.sub(
            r'\*(.*?)\*',
            r'<!-- ITALIC -->\1<!-- /ITALIC -->',
            content
        )
        
        return content
    
    def _handle_embedded_tables(self, content: str) -> str:
        """Handle tables embedded in Word documents"""
        # Similar to Excel table handling but simpler
        content = re.sub(
            r'((?:\|.*\|.*\|\n?){2,})',
            r'<!-- EMBEDDED_TABLE -->\1<!-- /EMBEDDED_TABLE -->',
            content,
            flags=re.MULTILINE
        )
        
        return content
    
    def _mark_document_sections(self, content: str) -> str:
        """Mark typical Word document sections"""
        # Mark introduction sections
        content = re.sub(
            r'(?i)(.*(?:introduction|overview|abstract|executive summary).*)',
            r'<!-- INTRO_SECTION -->\1<!-- /INTRO_SECTION -->',
            content,
            flags=re.MULTILINE
        )
        
        # Mark conclusion sections
        content = re.sub(
            r'(?i)(.*(?:conclusion|summary|recommendations|next steps).*)',
            r'<!-- CONCLUSION_SECTION -->\1<!-- /CONCLUSION_SECTION -->',
            content,
            flags=re.MULTILINE
        )
        
        return content