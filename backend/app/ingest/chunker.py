"""Semantic chunking for SocioGraph.

This module provides functions to split text into semantic chunks.
For simplicity, we use a paragraph-based approach rather than relying on
external dependencies.
"""

from typing import List
import re

from backend.app.core.singletons import get_logger

logger = get_logger()


def chunk_page(text: str) -> List[str]:
    """Split a page of text into semantic chunks.
    
    Args:
        text: The text to chunk
        
    Returns:
        List of chunks
    """
    logger.debug(f"Chunking text of length {len(text)}")
    
    # Simple paragraph-based chunking
    # First clean the text (remove excessive whitespace)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Try to split by paragraphs (double newlines)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    
    # If no paragraphs found, try single newlines
    if len(paragraphs) <= 1:
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    
    # If still no good chunks, break by sentences (roughly)
    if len(paragraphs) <= 1 and len(text) > 200:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > 200:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                    
        if current_chunk:
            chunks.append(current_chunk)
            
        logger.debug(f"Created {len(chunks)} chunks using sentence splitting")
        return chunks
    
    logger.debug(f"Created {len(paragraphs)} chunks using paragraph splitting")
    return paragraphs