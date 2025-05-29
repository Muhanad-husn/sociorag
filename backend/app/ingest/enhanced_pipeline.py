"""Enhanced ingestion pipeline for SocioGraph.

This module uses the enhanced entity extraction with:
- Retry mechanism
- Response caching
- Batch processing
- Structured error reporting
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
from backend.app.ingest.reset import reset_corpus
from backend.app.ingest.enhanced_entity_extraction import (
    extract_entities_from_text,
    batch_process_chunks
)


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


def add_chunks_to_store(chunks: List[str], source_file: str) -> None:
    """Add chunks to the vector store.
    
    Args:
        chunks: List of text chunks
        source_file: Source filename (without extension)
    """
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


def normalize_embedding(embedding: Any) -> List[float]:
    """Convert embedding to a standard list of floats.
    
    Args:
        embedding: The embedding from the model
        
    Returns:
        A list of floats
    """
    if isinstance(embedding, list):
        if not embedding:
            # Empty list
            return [0.0] * 384  # Default dimension for all-MiniLM-L6-v2
        elif isinstance(embedding[0], list):
            # List of lists, take first one
            return embedding[0]
        elif isinstance(embedding[0], (int, float)):
            # Already a list of numbers
            return embedding
    elif isinstance(embedding, np.ndarray):
        # Convert numpy array to list
        return embedding.tolist()
    
    # Fallback
    logger.warning(f"Unexpected embedding format: {type(embedding)}")
    return [0.0] * 384  # Default dimension


def get_or_insert_entity(surface: str, typ: str, source_doc: str) -> int:
    """Get an existing entity ID or insert a new entity.
    
    Uses vector similarity to deduplicate entities.
    
    Args:
        surface: Surface form of the entity
        typ: Entity type
        source_doc: Source document name
        
    Returns:
        Entity ID
    """
    con = get_sqlite()
    
    # Embed the entity text
    embedding_result = embed_texts(surface)
    
    # Normalize to a flat list of floats
    vec_new = normalize_embedding(embedding_result)
    
    # Convert to bytes for SQLite-vec
    vec_bytes = array('f', vec_new).tobytes()
    
    # Try to find similar entities using SQLite-vec
    try:
        # Try to use SQLite-vec for vector search if available
        cur = con.execute(
            """
            SELECT id, name, vec_cosine(embedding, ?) as similarity 
            FROM entity 
            WHERE type = ? 
            ORDER BY similarity DESC 
            LIMIT 5
            """,
            (vec_bytes, typ)
        )
        
        # Check if any entity is above similarity threshold
        rows = cur.fetchall()
        for row in rows:
            row_id = row[0]
            row_name = row[1]
            similarity = row[2]  # Similarity from vec_cosine
            
            # If similarity is above threshold, return existing ID
            if similarity >= config.ENTITY_SIM:  # 0.90
                logger.debug(f"Found similar entity: '{surface}' ~ '{row_name}' (sim={similarity:.3f})")
                return row_id
                
    except Exception as e:
        # Fall back to manual similarity calculation if SQLite-vec functions fail
        logger.warning(f"SQLite-vec search failed: {e}. Falling back to manual calculation.")
        
        cur = con.execute(
            "SELECT id, name, embedding FROM entity WHERE type = ?",
            (typ,)
        )
        
        # Check existing entities for similarity manually
        rows = cur.fetchall()
        for row in rows:
            row_id = row[0]
            row_name = row[1]
            row_embedding = row[2]
            
            # Skip if no embedding
            if not row_embedding:
                continue
                
            # Convert bytes back to list
            try:
                vec_existing = array('f', row_embedding).tolist()
                
                # Calculate similarity
                similarity = cosine_similarity(vec_new, vec_existing)
                
                # If similarity is above threshold, return existing ID
                if similarity >= config.ENTITY_SIM:  # 0.90
                    logger.debug(f"Found similar entity: '{surface}' ~ '{row_name}' (sim={similarity:.3f})")
                    return row_id
            except Exception as sim_err:
                logger.error(f"Error calculating similarity: {sim_err}")
      # If no similar entity found, insert new one
    try:
        cur = con.execute(
            "INSERT OR IGNORE INTO entity(name, type, embedding, source_doc) VALUES(?,?,?,?)",
            (surface, typ, vec_bytes, source_doc)
        )
        
        entity_id = cur.lastrowid
        
        # If INSERT OR IGNORE didn't insert (entity already exists), get existing ID
        if entity_id is None or entity_id == 0:
            cur = con.execute("SELECT id FROM entity WHERE name = ? AND type = ?", (surface, typ))
            row = cur.fetchone()
            if row:
                return row[0]
            else:
                logger.error(f"Failed to get or insert entity: {surface}")
                return -1
        
        return entity_id
        
    except Exception as e:
        logger.error(f"Error inserting entity '{surface}': {str(e)}")
        # Try to get existing entity
        try:
            cur = con.execute("SELECT id FROM entity WHERE name = ? AND type = ?", (surface, typ))
            row = cur.fetchone()
            if row:
                return row[0]
        except Exception as get_err:
            logger.error(f"Error getting existing entity '{surface}': {str(get_err)}")
        return -1


def insert_graph_rows(rows: List[Dict[str, str]], source_doc: str) -> None:
    """Insert entity and relation rows into the graph database.
    
    Args:
        rows: List of entity-relation objects
        source_doc: Source document name
    """
    con = get_sqlite()
    
    for obj in rows:
        # Get or insert head entity
        head_id = get_or_insert_entity(
            surface=obj["head"],
            typ=obj["head_type"],
            source_doc=source_doc
        )
        
        # Get or insert tail entity
        tail_id = get_or_insert_entity(
            surface=obj["tail"],
            typ=obj["tail_type"],
            source_doc=source_doc
        )
        
        # Skip if either entity failed to be created
        if head_id < 0 or tail_id < 0:
            continue
        
        # Insert relation
        con.execute(
            "INSERT OR IGNORE INTO relation(source_id, target_id, relation_type, source_doc) VALUES(?,?,?,?)",
            (head_id, tail_id, obj["relation"], source_doc)
        )
    
    # Commit transaction
    con.commit()


async def extract_entities_from_chunks(chunks: List[str], source_file: str) -> AsyncGenerator[Dict[str, Any], None]:
    """Extract entities and relationships from chunks.
    
    This function uses batch processing for better efficiency.
    
    Args:
        chunks: List of text chunks
        source_file: Source filename (without extension)
        
    Yields:
        Progress updates
    """
    logger.info(f"Extracting entities from {len(chunks)} chunks")
    
    # Calculate optimal batch size based on chunk count
    # Smaller batches for many chunks, larger for few
    batch_size = max(1, min(5, len(chunks) // 10))
    # Calculate optimal concurrency based on available resources
    concurrency = min(3, max(1, len(chunks) // 20))
    
    logger.info(f"Using batch size {batch_size} and concurrency {concurrency}")
    
    # Process chunks in optimized batches
    total_entities = 0
    processed_chunks = 0
    
    # Process in smaller sub-batches to provide more frequent progress updates
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1} ({len(batch)} chunks)")
        
        # Process the batch
        batch_results = await batch_process_chunks(batch, batch_size=batch_size, concurrency_limit=concurrency)
        
        # Insert entities for this batch
        for j, entities in enumerate(batch_results):
            chunk_index = i + j
            if entities:
                logger.info(f"Found {len(entities)} valid entity relationships in chunk {chunk_index+1}")
                insert_graph_rows(entities, source_file)
                total_entities += len(entities)
            else:
                logger.warning(f"No valid entities found in chunk {chunk_index+1}")
            
            processed_chunks += 1
            
            # Yield progress update
            progress = processed_chunks / len(chunks)
            yield {
                "phase": "extract_entities",
                "percent": round(progress * 100),
                "entities": total_entities,
                "processed_chunks": processed_chunks
            }
    
    logger.info(f"Extracted {total_entities} entity relationships from {processed_chunks} chunks")


def process_all() -> Generator[Dict[str, Any], None, None]:
    """Process all PDFs in the input directory.
    
    Yields:
        Progress updates as dictionaries
    """
    logger.info("Starting enhanced ingestion pipeline")
    
    # Get PDF files
    pdf_files = list(config.INPUT_DIR.glob("*.pdf"))
    total_files = len(pdf_files)
    
    if total_files == 0:
        logger.warning("No PDF files found in input directory")
        yield {"phase": "complete", "percent": 100}
        return
    
    logger.info(f"Found {total_files} PDF files to process")
    
    # Process each PDF
    total_chunks = 0
    total_entities = 0
    
    for i, pdf in enumerate(pdf_files):
        file_progress = i / total_files
        
        # Report progress
        yield {
            "phase": "loading",
            "percent": round(file_progress * 100),
            "file": pdf.name
        }
        
        # Load and chunk PDF
        pages = load_pages(pdf)
        chunks = []
        for page in pages:
            chunks.extend(chunk_page(page))
        
        total_chunks += len(chunks)
        
        # Add chunks to vector store
        add_chunks_to_store(chunks, pdf.stem)
        
        # Extract entities and relations with improved progress tracking
        async def process_entities():
            nonlocal total_entities
            async for progress in extract_entities_from_chunks(chunks, pdf.stem):
                # Update the total entities count
                total_entities = progress["entities"]
                # We don't yield here since this is called from within process_all
        
        # Run entity extraction
        asyncio.run(process_entities())
        
        # Report progress
        yield {
            "phase": "processing",
            "percent": round((i + 1) / total_files * 100),
            "file": pdf.name,
            "chunks": len(chunks),
            "entities": total_entities
        }
    
    # Final report
    yield {
        "phase": "complete",
        "percent": 100,
        "files": total_files,
        "chunks": total_chunks,
        "entities": total_entities
    }


async def process_entities(chunks: List[str], source_file: str) -> None:
    """Process entities from chunks asynchronously.
    
    Args:
        chunks: List of text chunks
        source_file: Source filename (without extension)
    """
    async for _ in extract_entities_from_chunks(chunks, source_file):
        # We don't need to yield progress here since this is an internal function
        pass
