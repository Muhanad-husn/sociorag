"""PDF loader for SocioGraph.

This module provides functions to load PDF documents and extract their text content.
"""

from pathlib import Path
from typing import List

from pypdf import PdfReader


def load_pages(pdf_path: Path) -> List[str]:
    """Load a PDF file and extract text from each page.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of strings, each containing the text from one page
    """
    reader = PdfReader(pdf_path)
    return [page.extract_text() or "" for page in reader.pages]