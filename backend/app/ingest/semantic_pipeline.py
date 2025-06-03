"""Enhanced semantic ingestion pipeline for SocioGraph.

This module provides an updated ingestion pipeline that uses:
- Semantic chunking with embedding similarity analysis
- Enhanced entity extraction with retry mechanisms
- Adaptive chunking based on document type
- Hybrid fallback for reliability
"""

import asyncio
import json
import math
import re
from array import array
from pathlib import Path
from typing import Dict, List, Any, Union, Optional, Generator, AsyncGenerator, Tuple

import numpy as np
from numpy.linalg import norm

from backend.app.core.config import get_config
from backend.app.core.singletons import (
    get_logger, 
    get_chroma, 
    embed_texts, 
    get_sqlite
)
from backend.app.ingest.loader import load_pages
from backend.app.ingest.chunker import chunk_page
from backend.app.ingest.semantic_chunker import HybridChunker, AdaptiveSemanticChunker, SemanticChunker
from backend.app.ingest.reset import reset_corpus
from backend.app.ingest.enhanced_entity_extraction import (
    extract_entities_from_text,
    batch_process_chunks
)
from backend.app.ingest.enhanced_pipeline import insert_graph_rows


logger = get_logger()
config = get_config()


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a = np.array(v1)
    b = np.array(v2)
    
    # Handle zero vectors
    if norm(a) == 0 or norm(b) == 0:
        return 0.0
        
    return float(np.dot(a, b) / (norm(a) * norm(b)))


class SemanticDocumentProcessor:
    """Enhanced document processor using semantic chunking."""
    
    def __init__(self):
        self.config = get_config()
        
        # Initialize the appropriate chunker based on configuration
        if self.config.SEMANTIC_CHUNKING_ENABLED:
            if self.config.HYBRID_CHUNKING_FALLBACK:
                self.chunker = HybridChunker(
                    buffer_size=self.config.SEMANTIC_CHUNK_BUFFER_SIZE,
                    breakpoint_percentile_threshold=self.config.SEMANTIC_CHUNK_THRESHOLD,
                    max_chunk_size=self.config.SEMANTIC_MAX_CHUNK_SIZE,
                    min_chunk_size=self.config.SEMANTIC_MIN_CHUNK_SIZE
                )
                logger.info("Initialized HybridChunker with semantic fallback")
            elif self.config.ADAPTIVE_CHUNKING:
                self.chunker = AdaptiveSemanticChunker(
                    buffer_size=self.config.SEMANTIC_CHUNK_BUFFER_SIZE,
                    breakpoint_percentile_threshold=self.config.SEMANTIC_CHUNK_THRESHOLD,
                    max_chunk_size=self.config.SEMANTIC_MAX_CHUNK_SIZE,
                    min_chunk_size=self.config.SEMANTIC_MIN_CHUNK_SIZE
                )
                logger.info("Initialized AdaptiveSemanticChunker")
            else:
                self.chunker = SemanticChunker(
                    buffer_size=self.config.SEMANTIC_CHUNK_BUFFER_SIZE,
                    breakpoint_percentile_threshold=self.config.SEMANTIC_CHUNK_THRESHOLD,
                    max_chunk_size=self.config.SEMANTIC_MAX_CHUNK_SIZE,
                    min_chunk_size=self.config.SEMANTIC_MIN_CHUNK_SIZE
                )
                logger.info("Initialized basic SemanticChunker")
        else:
            # Fallback to rule-based chunking
            self.chunker = None
            logger.info("Semantic chunking disabled, using rule-based chunking")
    
    def add_chunks_to_store(self, document_text: str, source: str) -> List[Dict[str, Any]]:
        """
        Process document with semantic chunking and add to vector store.
        
        Args:
            document_text: The full text content of the document
            source: Source identifier (filename without extension)
            
        Returns:
            List of processed chunks with metadata
        """
        logger.info(f"Processing document: {source}")
        
        # Use semantic chunking if enabled
        if self.config.SEMANTIC_CHUNKING_ENABLED and self.chunker:
            chunks_data = self.chunker.chunk_text(document_text, source)
            chunks = [chunk_data['content'] for chunk_data in chunks_data]
        else:
            # Fall back to rule-based chunking
            chunks = chunk_page(document_text)
            chunks_data = [
                {
                    'content': chunk,
                    'metadata': {
                        'source': source,
                        'chunk_index': i,
                        'chunk_type': 'rule_based',
                        'char_count': len(chunk),
                        'semantic_score': None
                    }
                }
                for i, chunk in enumerate(chunks)
            ]
        
        logger.info(f"Generated {len(chunks)} chunks from {source}")
        
        # Process chunks for vector store
        if chunks:
            # Create IDs and metadata for vector store
            ids = [f"{source}:{chunk_data['metadata']['chunk_index']}" for chunk_data in chunks_data]
            meta = [
                {
                    "text": chunk_data['content'], 
                    "file": source,
                    "chunk_type": chunk_data['metadata']['chunk_type'],
                    "char_count": chunk_data['metadata']['char_count'],
                    "semantic_score": chunk_data['metadata'].get('semantic_score')
                } 
                for chunk_data in chunks_data
            ]
            
            # Add to Chroma vector store
            chroma = get_chroma()
            chroma.add_texts(
                texts=chunks,
                metadatas=meta,
                ids=ids
            )
            
            logger.info(f"Added {len(chunks)} chunks to vector store")
        
        return chunks_data


# Initialize global processor instance
_semantic_processor = None

def get_semantic_processor() -> SemanticDocumentProcessor:
    """Get singleton semantic document processor."""
    global _semantic_processor
    if _semantic_processor is None:
        _semantic_processor = SemanticDocumentProcessor()
    return _semantic_processor


def add_chunks_to_store_semantic(chunks: List[str], source_file: str) -> None:
    """
    Legacy interface: Add chunks to the vector store using semantic processing.
    
    This maintains compatibility with existing code while using the new processor.
    
    Args:
        chunks: List of text chunks (will be joined for semantic processing)
        source_file: Source filename (without extension)
    """
    logger.info(f"Processing {len(chunks)} pre-chunked texts from {source_file}")
    
    # Join chunks back into document text for semantic processing
    document_text = "\n\n".join(chunks)
    
    # Use semantic processor
    processor = get_semantic_processor()
    processor.add_chunks_to_store(document_text, source_file)


def add_chunks_to_store(chunks: List[str], source_file: str) -> None:
    """
    Add chunks to the vector store.
    
    This function now routes to semantic processing if enabled,
    maintaining backward compatibility.
    
    Args:
        chunks: List of text chunks
        source_file: Source filename (without extension)
    """
    config = get_config()
    
    if config.SEMANTIC_CHUNKING_ENABLED:
        # Use semantic processing
        add_chunks_to_store_semantic(chunks, source_file)
    else:
        # Use original implementation
        logger.info(f"Adding {len(chunks)} chunks from {source_file} to vector store")
        
        if not chunks:
            logger.warning("No chunks to add")
            return
            
        # Create IDs and metadata
        ids = [f"{source_file}:{i}" for i in range(len(chunks))]
        meta = [{"text": c, "file": source_file} for c in chunks]
        
        # Add to Chroma using add_texts which accepts string documents
        chroma = get_chroma()
        chroma.add_texts(
            texts=chunks,
            metadatas=meta,
            ids=ids
        )
        
        logger.info(f"Added {len(chunks)} chunks to vector store")


async def run_semantic_pipeline(input_dir: Optional[Path] = None, reset: bool = False) -> Dict[str, Any]:
    """
    Run the complete semantic ingestion pipeline.
    
    Args:
        input_dir: Directory containing PDF files (defaults to config.INPUT_DIR)
        reset: Whether to reset the corpus before processing
        
    Returns:
        Dictionary with processing statistics
    """
    if input_dir is None:
        input_dir = config.INPUT_DIR
    
    logger.info(f"Starting semantic ingestion pipeline from {input_dir}")
    
    if reset:
        logger.info("Resetting corpus before processing")
        reset_corpus()
      # Initialize processor
    processor = get_semantic_processor()
    
    # Get PDF files to process
    pdf_files = list(input_dir.glob("*.pdf"))
    total_files = len(pdf_files)
    
    if total_files == 0:
        logger.warning("No PDF files found in input directory")
        return {
            "processed_files": 0,
            "total_chunks": 0,
            "total_entities": 0,
            "chunking_method": "semantic" if config.SEMANTIC_CHUNKING_ENABLED else "rule_based",
            "adaptive_chunking": config.ADAPTIVE_CHUNKING,
            "hybrid_fallback": config.HYBRID_CHUNKING_FALLBACK
        }
    
    logger.info(f"Found {total_files} PDF files to process")
    
    total_chunks = 0
    total_entities = 0
    processed_files = 0
    
    stats = {
        "processed_files": 0,
        "total_chunks": 0,
        "total_entities": 0,
        "chunking_method": "semantic" if config.SEMANTIC_CHUNKING_ENABLED else "rule_based",
        "adaptive_chunking": config.ADAPTIVE_CHUNKING,
        "hybrid_fallback": config.HYBRID_CHUNKING_FALLBACK
    }
    
    # Process each PDF file
    for pdf_file in pdf_files:
        filename = pdf_file.name
        
        # Load pages from the PDF file
        pages = load_pages(pdf_file)
        
        # Combine all pages into a single text for processing
        text = "\n\n".join(pages)
        try:
            logger.info(f"Processing file: {filename}")
              # Process with semantic chunking
            chunks_data = processor.add_chunks_to_store(text, filename)
            total_chunks += len(chunks_data)
            stats["total_chunks"] = total_chunks
            
            # Extract entities from chunks
            chunks_text = [chunk_data['content'] for chunk_data in chunks_data]
            entities_result = await batch_process_chunks(chunks_text)
            
            # Count total entities and insert them into database
            entities_count = 0
            for chunk_entities in entities_result:
                if chunk_entities:
                    # Insert entities for this chunk into the database
                    insert_graph_rows(chunk_entities, filename)
                    entities_count += len(chunk_entities)
            
            total_entities += entities_count
            stats["total_entities"] = total_entities
            
            processed_files += 1
            stats["processed_files"] = processed_files
            
            logger.info(f"Completed processing {filename}: {len(chunks_data)} chunks, {entities_count} entities")
            
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            continue
    
    logger.info(f"Semantic pipeline completed: {processed_files} files, {total_chunks} chunks, {total_entities} entities")
    return stats


# Backward compatibility functions
async def run_enhanced_pipeline(input_dir: Optional[Path] = None, reset: bool = False) -> Dict[str, Any]:
    """Backward compatibility wrapper for run_semantic_pipeline."""
    return await run_semantic_pipeline(input_dir, reset)


# Import and run functions for compatibility
def run_semantic_ingest():
    """Run semantic ingestion pipeline synchronously."""
    import asyncio
    return asyncio.run(run_semantic_pipeline())


if __name__ == "__main__":
    # Run the semantic pipeline
    stats = run_semantic_ingest()
    print(f"Processing complete: {stats}")
