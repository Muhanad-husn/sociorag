"""PDF loader for SocioGraph.

This module provides functions to load PDF documents and extract their text content.
"""

import unicodedata
from pathlib import Path
from typing import List

from pypdf import PdfReader


def normalize_text(text: str) -> str:
    """Normalize text to handle encoding issues and special characters.
    
    Args:
        text: The text to normalize
        
    Returns:
        Normalized text with proper UTF-8 encoding
    """
    if not text:
        return ""
    
    # Normalize Unicode characters (handle special characters like ■)
    normalized = unicodedata.normalize('NFKC', text)
    
    # Replace common problematic characters
    replacements = {
        '■': '-',  # Replace box character with hyphen
        '□': '-',  # Replace empty box with hyphen
        '▪': '-',  # Replace small square with hyphen
        '▫': '-',  # Replace small square with hyphen
        '\ufeff': '',  # Remove BOM (Byte Order Mark)
        '\u00a0': ' ',  # Replace non-breaking space with regular space
        '\u2000': ' ',  # En quad
        '\u2001': ' ',  # Em quad
        '\u2002': ' ',  # En space
        '\u2003': ' ',  # Em space
        '\u2004': ' ',  # Three-per-em space
        '\u2005': ' ',  # Four-per-em space
        '\u2006': ' ',  # Six-per-em space
        '\u2007': ' ',  # Figure space
        '\u2008': ' ',  # Punctuation space
        '\u2009': ' ',  # Thin space
        '\u200a': ' ',  # Hair space
        '\u200b': '',   # Zero width space
        '\u200c': '',   # Zero width non-joiner
        '\u200d': '',   # Zero width joiner
    }
    
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    
    # Ensure proper encoding by encoding to UTF-8 and decoding back
    try:
        normalized = normalized.encode('utf-8', errors='replace').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Fallback: remove any problematic characters
        normalized = ''.join(char for char in normalized if ord(char) < 65536)
    
    return normalized


def load_pages(pdf_path: Path) -> List[str]:
    """Load a PDF file and extract text from each page.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of strings, each containing the text from one page
    """
    reader = PdfReader(pdf_path)
    pages = []
    
    for page in reader.pages:
        text = page.extract_text() or ""
        # Normalize the text to handle encoding issues
        normalized_text = normalize_text(text)
        pages.append(normalized_text)
    
    return pages