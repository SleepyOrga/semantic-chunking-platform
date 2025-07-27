class OCRPreprocessor:
    """Preprocessing steps for OCR-derived markdown content"""
    
    def preprocess_ocr_markdown(self, content: str) -> tuple[str, dict]:
        """
        Preprocessing steps for OCR-derived markdown
        """
        enhanced_content = content
        metadata = {
            'preprocessing_steps': [],
            'detected_patterns': {},
            'ocr_confidence': 'unknown'
        }
        
        # Step 1: Aggressive OCR error correction
        enhanced_content, correction_stats = self._correct_ocr_errors(enhanced_content)
        metadata['preprocessing_steps'].append('ocr_error_correction')
        metadata['detected_patterns'].update(correction_stats)
        
        # Step 2: Reconstruct broken text
        enhanced_content = self._reconstruct_broken_text(enhanced_content)
        metadata['preprocessing_steps'].append('text_reconstruction')
        
        # Step 3: Handle poor spacing
        enhanced_content = self._fix_spacing_issues(enhanced_content)
        metadata['preprocessing_steps'].append('spacing_correction')
        
        # Step 4: Identify and preserve structure
        enhanced_content = self._identify_document_structure(enhanced_content)
        metadata['preprocessing_steps'].append('structure_identification')
        
        # Step 5: Mark uncertain sections
        enhanced_content, confidence_data = self._mark_low_confidence_sections(enhanced_content)
        metadata['preprocessing_steps'].append('confidence_marking')
        metadata['ocr_confidence'] = confidence_data.get('average_confidence', 'low')
        
        return enhanced_content, metadata
    
    def _correct_ocr_errors(self, content: str) -> tuple[str, dict]:
        """Correct common OCR errors"""
        corrections_made = 0
        
        # Common OCR character mistakes
        ocr_corrections = {
            r'\b0(?=[a-zA-Z])': 'O',  # 0 instead of O at start of words
            r'(?<=[a-zA-Z])0\b': 'o',  # 0 instead of o at end of words
            r'\bl(?=[A-Z])': 'I',      # lowercase l instead of I
            r'rn(?=[a-z])': 'm',       # rn instead of m
            r'\|(?=[a-zA-Z])': 'l',    # | instead of l
            r'(?<=[a-zA-Z])\|': 'l',   # | instead of l
            r'\bvv': 'w',              # vv instead of w
            r'\bc1': 'cl',             # c1 instead of cl
            r'\bd1': 'dl',             # d1 instead of dl
        }
        
        for wrong, correct in ocr_corrections.items():
            old_content = content
            content = re.sub(wrong, correct, content, flags=re.IGNORECASE)
            if content != old_content:
                corrections_made += 1
        
        return content, {'ocr_corrections_made': corrections_made}
    
    def _reconstruct_broken_text(self, content: str) -> str:
        """Reconstruct text broken by poor OCR"""
        lines = content.split('\n')
        reconstructed_lines = []
        
        i = 0
        while i < len(lines):
            current_line = lines[i].strip()
            
            # Skip empty lines
            if not current_line:
                reconstructed_lines.append('')
                i += 1
                continue
            
            # Check if line seems incomplete (short line that doesn't end with punctuation)
            if (len(current_line) < 60 and 
                not current_line.endswith(('.', '!', '?', ':', ';')) and
                i + 1 < len(lines) and
                lines[i + 1].strip() and
                not lines[i + 1].startswith('#')):
                
                # Try to join with next line
                next_line = lines[i + 1].strip()
                if not next_line[0].isupper() or len(current_line) < 30:
                    current_line += ' ' + next_line
                    i += 2
                else:
                    i += 1
            else:
                i += 1
            
            reconstructed_lines.append(current_line)
        
        return '\n'.join(reconstructed_lines)
    
    def _fix_spacing_issues(self, content: str) -> str:
        """Fix spacing issues common in OCR"""
        # Fix multiple spaces
        content = re.sub(r' {2,}', ' ', content)
        
        # Fix spaces before punctuation
        content = re.sub(r' +([,.!?;:])', r'\1', content)
        
        # Fix missing spaces after punctuation
        content = re.sub(r'([.!?])([A-Z])', r'\1 \2', content)
        
        # Fix excessive line breaks
        content = re.sub(r'\n{4,}', '\n\n\n', content)
        
        return content
    
    def _identify_document_structure(self, content: str) -> str:
        """Try to identify document structure from OCR text"""
        lines = content.split('\n')
        enhanced_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # Identify potential headers (short lines, possibly all caps)
            if (line_stripped and 
                len(line_stripped) < 80 and 
                (line_stripped.isupper() or 
                 len([w for w in line_stripped.split() if w[0].isupper()]) > len(line_stripped.split()) * 0.7)):
                
                enhanced_lines.append("<!-- POTENTIAL_HEADER -->")
                enhanced_lines.append(line)
                enhanced_lines.append("<!-- /POTENTIAL_HEADER -->")
            else:
                enhanced_lines.append(line)
        
        return '\n'.join(enhanced_lines)
    
    def _mark_low_confidence_sections(self, content: str) -> tuple[str, dict]:
        """Mark sections that might have low OCR confidence"""
        # Look for indicators of poor OCR
        low_confidence_indicators = [
            r'[^\w\s.,!?;:()-]{2,}',  # Multiple special characters
            r'\w{15,}',                # Very long words (likely OCR errors)
            r'[0-9][a-zA-Z]{3,}[0-9]', # Numbers mixed with letters
            r'\b\w{1,2}\b.*\b\w{1,2}\b.*\b\w{1,2}\b'  # Many very short words
        ]
        
        suspicious_sections = 0
        for pattern in low_confidence_indicators:
            matches = re.findall(pattern, content)
            suspicious_sections += len(matches)
        
        # Mark very suspicious looking text
        content = re.sub(
            r'([^\w\s.,!?;:()-]{3,})',
            r'<!-- LOW_CONFIDENCE -->\1<!-- /LOW_CONFIDENCE -->',
            content
        )
        
        confidence_level = 'high' if suspicious_sections < 5 else 'medium' if suspicious_sections < 15 else 'low'
        
        return content, {
            'suspicious_sections': suspicious_sections,
            'average_confidence': confidence_level
        }