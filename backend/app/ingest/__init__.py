"""Ingest package for SocioGraph.

This package provides functionality for:
1. Loading PDF documents
2. Chunking text into semantic units
3. Embedding chunks and storing them in a vector database
4. Extracting entities and relationships (standard and enhanced)
5. Building a knowledge graph
"""

from .reset import reset_corpus
from .loader import load_pages
from .chunker import chunk_page
from .pipeline import (
    process_all,
    add_chunks_to_store,
    extract_entities_from_chunks,
    insert_graph_rows,
    get_or_insert_entity,
    normalize_embedding,
    cosine_similarity,
    process_entities
)
from .entity_extraction import extract_entities_from_text
from .enhanced_entity_extraction import (
    extract_entities_with_retry,
    batch_process_chunks,
    clear_cache
)
from .enhanced_pipeline import (
    process_all as enhanced_process_all,
    extract_entities_from_chunks as enhanced_extract_entities_from_chunks
)

__all__ = [
    "reset_corpus",
    "load_pages",
    "chunk_page",
    "process_all",
    "add_chunks_to_store",
    "extract_entities_from_chunks",
    "extract_entities_from_text",
    "insert_graph_rows",
    "get_or_insert_entity",
    "normalize_embedding",
    "cosine_similarity",
    "process_entities",
    # Enhanced entity extraction
    "extract_entities_with_retry",
    "batch_process_chunks",
    "clear_cache",
    "enhanced_process_all",
    "enhanced_extract_entities_from_chunks"
]