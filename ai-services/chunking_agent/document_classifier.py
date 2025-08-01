import logging
import re

logger = logging.getLogger(__name__)

from enum import Enum, auto

class DocumentType(Enum):
    SIMPLE = "SIMPLE"      # Small documents (<20KB)
    TECHNICAL = "TECHNICAL"  # Medium documents (20-50KB)
    COMPLEX = "COMPLEX"    # Large documents (>50KB)

class DocumentClassifier:
    @staticmethod
    def detect_document_type(content: str) -> DocumentType:
        print(f"[DEBUG] Detecting document type based on content length")
        if not content:
            logger.error("Empty content provided for document type detection")
            return DocumentType.SIMPLE
        char_count = len(content)
        print(f"Document character count: {char_count}")
        
        # Simple size-based decision
        if char_count > 5000:  # Very large documents (>50KB)
            return DocumentType.COMPLEX
        elif char_count > 3000:  # Medium-large documents (20-50KB)
            return DocumentType.TECHNICAL
        else:  # Small documents (<20KB)
            return DocumentType.SIMPLE


    @staticmethod
    def get_recommended_models(doc_type: DocumentType) -> list[str]:
        # Simple mapping based on document size
        mapping = {
            'SIMPLE': [  # For small documents (<20KB) - fast processing
                'us.anthropic.claude-3-5-haiku-20241022-v1:0'  # Fastest model
            ],
            'TECHNICAL': [  # For medium documents (20-50KB)
                'us.anthropic.claude-3-5-sonnet-20240620-v1:0',
                'us.anthropic.claude-3-7-sonnet-20250219-v1:0',
                'us.anthropic.claude-3-sonnet-20240229-v1:0'
            ],
            'COMPLEX': [  # For large documents (>50KB)
                'us.anthropic.claude-3-7-sonnet-20250219-v1:0',
                'us.anthropic.claude-sonnet-4-20250514-v1:0',
                'us.anthropic.claude-opus-4-20250514-v1:0',
            ]
        }
        # Use the enum value to get the recommended models
        return mapping.get(doc_type.value, ['us.anthropic.claude-3-5-sonnet-20240620-v1:0'])
