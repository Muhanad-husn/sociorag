"""Ingestion pipeline for SocioGraph.

This module orchestrates the full ingestion process:
1. Load PDFs from the input directory
2. Chunk the text into semantic units
3. Embed the chunks and add them to the vector store
4. Extract entities and relationships
5. Store the knowledge graph in SQLite
"""

import numpy as np
import asyncio
import json
import math
import re
from array import array
from pathlib import Path
from typing import Dict, List, Any, Union, Optional, Generator, AsyncGenerator, Tuple

from backend.app.core.config import get_config
from backend.app.core.singletons import (
    get_logger, 
    get_chroma, 
    embed_texts, 
    get_sqlite,
    get_llm_client
)
from backend.app.retriever.vector_utils import calculate_cosine_similarity
from backend.app.prompts import graph_prompts as gp
from backend.app.ingest.loader import load_pages
from backend.app.ingest.chunker import chunk_page
from backend.app.ingest.reset import reset_corpus
from backend.app.ingest.entity_extraction import extract_entities_from_text


logger = get_logger()
config = get_config()


# Import semantic chunking components
try:
    from backend.app.ingest.semantic_pipeline import (
        add_chunks_to_store as add_chunks_to_store_semantic,
        run_semantic_pipeline,
        get_semantic_processor
    )
    SEMANTIC_CHUNKING_AVAILABLE = True
    logger.info("Semantic chunking modules loaded successfully")
except ImportError as e:
    SEMANTIC_CHUNKING_AVAILABLE = False
    logger.warning(f"Semantic chunking not available: {e}")


from backend.app.retriever.vector_utils import calculate_cosine_similarity

# Use the centralized cosine similarity function
cosine_similarity = calculate_cosine_similarity


def add_chunks_to_store(chunks: List[str], source_file: str) -> None:
    """Add chunks to the vector store.
    
    This function now routes to semantic processing if enabled,
    maintaining backward compatibility.
    
    Args:
        chunks: List of text chunks
        source_file: Source filename (without extension)
    """
    # Route to semantic processing if available and enabled
    if (SEMANTIC_CHUNKING_AVAILABLE and 
        config.SEMANTIC_CHUNKING_ENABLED and 
        hasattr(config, 'SEMANTIC_CHUNKING_ENABLED')):
        logger.info(f"Routing to semantic chunking for {source_file}")
        add_chunks_to_store_semantic(chunks, source_file)
        return
    
    # Original implementation for backward compatibility
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


def clean_json_response(raw_response: str) -> str:
    """Clean a JSON response from an LLM.
    
    This handles common issues like markdown code blocks, extra text,
    and malformed JSON to extract the best possible JSON content.
    
    Args:
        raw_response: The raw response from the LLM
        
    Returns:
        Cleaned JSON string ready for parsing
    """
    # Log raw response for debugging
    logger.debug(f"Raw LLM response: {raw_response}")
    
    # Step 1: Remove markdown code blocks
    # This handles ```json and ``` patterns
    response = re.sub(r'```(?:json)?\s*|\s*```', '', raw_response)
    
    # Step 2: Try to extract just the JSON array
    # Look for a pattern that starts with [ and ends with ]
    json_array_match = re.search(r'\[(.*)\]', response, re.DOTALL)
    if json_array_match:
        response = f"[{json_array_match.group(1)}]"
    
    # Step 3: Fix common JSON syntax errors
    # Fix missing quotes around keys
    response = re.sub(r'(?<=[{,])\s*(\w+):', r'"\1":', response)
    
    # Fix trailing commas in arrays/objects
    response = re.sub(r',\s*([}\]])', r'\1', response)
    
    # Step 4: Remove any non-JSON text before or after the array
    response = response.strip()
    if not (response.startswith('[') and response.endswith(']')):
        # If we don't have a clean JSON array, try to find one
        start = response.find('[')
        end = response.rfind(']')
        if start >= 0 and end > start:
            response = response[start:end+1]
    
    # Step 5: Final clean-up
    response = response.strip()
    
    logger.debug(f"Cleaned JSON: {response}")
    return response


def validate_entity_object(obj: Dict[str, Any]) -> bool:
    """Validate that an entity object has all required fields.
    
    Args:
        obj: The entity object to validate
        
    Returns:
        True if valid, False if not
    """
    required_fields = ["head", "head_type", "relation", "tail", "tail_type"]
    return all(field in obj for field in required_fields)


def safe_parse_json(json_str: str) -> Tuple[List[Dict[str, str]], bool]:
    """Safely parse JSON, with fallback strategies for malformed JSON.
    
    Args:
        json_str: JSON string to parse
        
    Returns:
        Tuple of (parsed_data, success_flag)
    """
    # First try: standard JSON parsing
    try:
        data = json.loads(json_str)
        if isinstance(data, list):
            # Validate each object in the list
            valid_objects = [obj for obj in data if validate_entity_object(obj)]
            if valid_objects:
                return valid_objects, True
    except json.JSONDecodeError:
        logger.warning(f"Standard JSON parsing failed")
    
    # Second try: repair and parse line by line
    # This handles cases where some objects are valid and some are not
    try:
        # Split by objects (looking for pattern like }, {)
        object_pattern = re.compile(r'},\s*{')
        parts = object_pattern.split(json_str.strip('[]'))
        
        # Repair and parse each object
        valid_objects = []
        for i, part in enumerate(parts):
            # Add opening/closing braces if needed
            if not part.startswith('{'):
                part = '{' + part
            if not part.endswith('}'):
                part = part + '}'
                
            try:
                obj = json.loads(part)
                if validate_entity_object(obj):
                    valid_objects.append(obj)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse object {i+1}")
        
        if valid_objects:
            return valid_objects, True
    except Exception as e:
        logger.warning(f"Object-by-object parsing failed: {e}")
    
    # If all parsing attempts fail, return empty list
    return [], False


async def extract_entities_from_chunks(chunks: List[str], source_file: str) -> AsyncGenerator[Dict[str, Any], None]:
    """Extract entities and relationships from chunks.
    
    Args:
        chunks: List of text chunks
        source_file: Source filename (without extension)
        
    Yields:
        Progress updates
    """
    logger.info(f"Extracting entities from {len(chunks)} chunks")
    
    total_entities = 0
    for i, chunk in enumerate(chunks):
        logger.debug(f"Processing chunk {i+1}/{len(chunks)}")
        
        # Use the improved entity extraction function
        rows = await extract_entities_from_text(chunk)
        
        if rows:
            # Insert rows into graph
            logger.info(f"Found {len(rows)} valid entity relationships in chunk {i+1}")
            insert_graph_rows(rows, source_file)
            total_entities += len(rows)
        else:
            logger.warning(f"No valid entities found in chunk {i+1}")
            
        # Yield progress update
        progress = (i + 1) / len(chunks)
        yield {
            "phase": "extract_entities",
            "percent": round(progress * 100),
            "entities": total_entities
        }
    
    logger.info(f"Extracted {total_entities} entity relationships")


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
    
    # Convert to bytes for storage
    vec_bytes = array('f', vec_new).tobytes()
    
    # Use manual similarity calculation
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


def process_all() -> Generator[Dict[str, Any], None, None]:
    """Process all PDFs in the input directory.
    
    Yields:
        Progress updates as dictionaries
    """
    logger.info("Starting ingestion pipeline")
    
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
        
        # Extract entities and relations
        asyncio.run(process_entities(chunks, pdf.stem))
        
        # Report progress
        yield {
            "phase": "processing",
            "percent": round((i + 1) / total_files * 100),
            "file": pdf.name,
            "chunks": len(chunks)
        }
    
    # Final report
    yield {
        "phase": "complete",
        "percent": 100,
        "files": total_files,
        "chunks": total_chunks
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


async def run_pipeline(input_dir: Optional[Path] = None, reset: bool = False, use_semantic: Optional[bool] = None) -> Dict[str, Any]:
    """
    Run the appropriate ingestion pipeline based on configuration.
    
    Args:
        input_dir: Directory containing PDF files (defaults to config.INPUT_DIR)
        reset: Whether to reset the corpus before processing
        use_semantic: Force semantic chunking on/off, or None to use config
        
    Returns:
        Dictionary with processing statistics
    """
    # Determine which pipeline to use
    should_use_semantic = use_semantic
    if should_use_semantic is None:
        should_use_semantic = (
            SEMANTIC_CHUNKING_AVAILABLE and 
            getattr(config, 'SEMANTIC_CHUNKING_ENABLED', False)
        )
    
    if should_use_semantic and SEMANTIC_CHUNKING_AVAILABLE:
        logger.info("Running semantic ingestion pipeline")
        return await run_semantic_pipeline(input_dir, reset)
    else:
        logger.info("Running traditional rule-based ingestion pipeline")
        return await run_traditional_pipeline(input_dir, reset)


async def run_traditional_pipeline(input_dir: Optional[Path] = None, reset: bool = False) -> Dict[str, Any]:
    """
    Run the traditional rule-based ingestion pipeline.
    
    Args:
        input_dir: Directory containing PDF files (defaults to config.INPUT_DIR)
        reset: Whether to reset the corpus before processing
        
    Returns:
        Dictionary with processing statistics
    """
    if input_dir is None:
        input_dir = config.INPUT_DIR
    
    logger.info(f"Starting traditional ingestion pipeline from {input_dir}")
    
    if reset:
        logger.info("Resetting corpus before processing")
        reset_corpus()
    
    # Load and process documents
    pages = load_pages(input_dir)
    total_chunks = 0
    total_entities = 0
    processed_files = 0
    
    stats = {
        "processed_files": 0,
        "total_chunks": 0,
        "total_entities": 0,
        "chunking_method": "rule_based",
        "adaptive_chunking": False,
        "hybrid_fallback": False
    }
    
    for filename, text in pages:
        try:
            logger.info(f"Processing file: {filename}")
            
            # Chunk using traditional method
            chunks = chunk_page(text)
            total_chunks += len(chunks)
            stats["total_chunks"] = total_chunks
            
            # Add to vector store
            add_chunks_to_store(chunks, filename)
            
            # Extract entities from chunks  
            entities_count = 0
            async for progress in extract_entities_from_chunks(chunks, filename):
                if "entities" in progress:
                    entities_count = progress["entities"]
            
            total_entities += entities_count
            stats["total_entities"] = total_entities
            
            processed_files += 1
            stats["processed_files"] = processed_files
            
            logger.info(f"Completed processing {filename}: {len(chunks)} chunks, {entities_count} entities")
            
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            continue
    
    logger.info(f"Traditional pipeline completed: {processed_files} files, {total_chunks} chunks, {total_entities} entities")
    return stats


# Backward compatibility functions
def run_ingest():
    """Run ingestion pipeline synchronously with current configuration."""
    import asyncio
    return asyncio.run(run_pipeline())


def run_ingest_semantic():
    """Run semantic ingestion pipeline synchronously."""
    import asyncio
    return asyncio.run(run_pipeline(use_semantic=True))


def run_ingest_traditional():
    """Run traditional rule-based ingestion pipeline synchronously."""
    import asyncio
    return asyncio.run(run_pipeline(use_semantic=False))


if __name__ == "__main__":
    # Run the appropriate pipeline based on configuration
    stats = run_ingest()
    print(f"Processing complete: {stats}")
