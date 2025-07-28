class PDFPreprocessor:
    """Preprocessing steps for PDF-derived markdown content"""
    
    def preprocess_pdf_markdown(self, content: str) -> tuple[str, dict]:
        """
        Preprocessing steps for PDF-derived markdown
        """
        enhanced_content = content
        metadata = {
            'preprocessing_steps': [],
            'detected_patterns': {}
        }
        
        # Step 1: Clean OCR artifacts
        enhanced_content = self._clean_ocr_artifacts(enhanced_content)
        metadata['preprocessing_steps'].append('ocr_cleaning')
        
        # Step 2: Fix page breaks and headers/footers
        enhanced_content = self._fix_page_elements(enhanced_content)
        metadata['preprocessing_steps'].append('page_elements_cleanup')
        
        # Step 3: Reconstruct paragraphs broken by page breaks
        enhanced_content = self._reconstruct_paragraphs(enhanced_content)
        metadata['preprocessing_steps'].append('paragraph_reconstruction')
        
        # Step 4: Handle multi-column layouts
        enhanced_content = self._handle_columns(enhanced_content)
        metadata['preprocessing_steps'].append('column_handling')
        
        # Step 5: Preserve document structure
        enhanced_content = self._preserve_pdf_structure(enhanced_content)
        metadata['preprocessing_steps'].append('structure_preservation')
        
        return enhanced_content, metadata
    
    def _clean_ocr_artifacts(self, content: str) -> str:
        """Clean common OCR artifacts"""
        # Remove extra spaces
        content = re.sub(r' +', ' ', content)
        
        # Fix broken words (common OCR issue)
        content = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', content)
        
        # Remove isolated single characters (OCR noise)
        content = re.sub(r'\n\s*[a-zA-Z]\s*\n', '\n', content)
        
        # Fix common OCR character mistakes
        ocr_fixes = {
            r'\b0\b': 'O',  # Zero instead of O
            r'\bl\b': 'I',  # lowercase l instead of I
            r'rn': 'm',     # rn instead of m
        }
        
        for wrong, correct in ocr_fixes.items():
            content = re.sub(wrong, correct, content)
        
        return content
    
    def _fix_page_elements(self, content: str) -> str:
        """Remove page headers, footers, and page numbers"""
        lines = content.split('\n')
        cleaned_lines = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip page numbers
            if re.match(r'^\s*\d+\s*$', line):
                continue
            
            # Skip common header/footer patterns
            if (re.match(r'(?i)page \d+', line) or
                re.match(r'(?i)confidential|proprietary|internal', line) or
                len(line) > 0 and len(line) < 5 and line.isdigit()):
                continue
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _reconstruct_paragraphs(self, content: str) -> str:
        """Reconstruct paragraphs broken by page breaks"""
        # Join lines that seem to be part of the same paragraph
        lines = content.split('\n')
        reconstructed_lines = []
        
        i = 0
        while i < len(lines):
            current_line = lines[i].strip()
            
            if not current_line:
                reconstructed_lines.append('')
                i += 1
                continue
            
            # Check if next line continues the paragraph
            if (i + 1 < len(lines) and 
                lines[i + 1].strip() and
                not lines[i + 1].startswith('#') and
                not current_line.endswith('.') and
                not current_line.endswith(':') and
                len(current_line) > 40):  # Likely incomplete line
                
                # Join with next line
                current_line += ' ' + lines[i + 1].strip()
                i += 2
            else:
                i += 1
            
            reconstructed_lines.append(current_line)
        
        return '\n'.join(reconstructed_lines)
    
    def _handle_columns(self, content: str) -> str:
        """Handle multi-column PDF layouts"""
        # This is complex and would need more sophisticated logic
        # For now, just ensure proper spacing between sections
        content = re.sub(r'\n{3,}', '\n\n', content)
        return content
    
    def _preserve_pdf_structure(self, content: str) -> str:
        """Add markers to preserve PDF document structure"""
        # Mark potential section breaks
        content = re.sub(
            r'(^.{10,80}$)(?=\n\n)',
            r'<!-- SECTION_HEADER -->\1<!-- /SECTION_HEADER -->',
            content,
            flags=re.MULTILINE
        )
        
        return content