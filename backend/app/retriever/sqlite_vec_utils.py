"""
SQLite vector utilities for SocioGraph with parallel processing.

This module provides optimized functions for working with vector embeddings
in SQLite, leveraging the EmbeddingSingleton for consistent embedding operations
and parallel processing for performance.
"""

from array import array
from typing import List, Union, Dict, Any, Optional, Tuple
import sqlite3
import concurrent.futures
from functools import partial

from backend.app.core.singletons import get_logger, get_sqlite, embed_texts
from backend.app.retriever.vector_utils import calculate_cosine_similarity, extract_vector

try:
    import sqlite_vec
except ImportError:
    sqlite_vec = None

# Initialize logger
_logger = get_logger()

def embedding_to_binary(embedding: Union[List[float], List[List[float]]]) -> bytes:
    """Convert embedding vector to binary blob for SQLite storage.
    
    Args:
        embedding: List of float values representing an embedding vector
        
    Returns:
        Binary blob representation of the embedding vector
    """
    # Extract vector to ensure we have a flat list
    vec = extract_vector(embedding)
    
    # Convert to array of floats, then to binary
    try:
        return array('f', vec).tobytes()
    except Exception as e:
        _logger.error(f"Error converting embedding to binary: {e}")
        return b''

def binary_to_embedding(binary_data: bytes) -> Optional[List[float]]:
    """Convert binary blob from SQLite to embedding vector.
    
    Args:
        binary_data: Binary blob representation of an embedding vector
        
    Returns:
        List of float values representing the embedding vector or None if conversion fails
    """
    if not binary_data:
        return None
        
    try:
        # Convert binary to array of floats, then to list
        return array('f', binary_data).tolist()
    except Exception as e:
        _logger.error(f"Error converting binary to embedding: {e}")
        return None

def _process_entity_batch(
    batch: List[sqlite3.Row], 
    query_embedding: Union[List[float], List[List[float]]], 
    similarity_threshold: float
) -> List[Dict[str, Any]]:
    """Process a batch of entities to calculate similarities.
    
    This is designed to be used with parallel processing.
    
    Args:
        batch: List of entity rows from database
        query_embedding: Embedding vector for the query
        similarity_threshold: Minimum similarity score to include
        
    Returns:
        List of entity records with similarity >= similarity_threshold
    """
    results = []
    for row in batch:
        entity_embedding = binary_to_embedding(row['embedding'])
        if entity_embedding:
            similarity = calculate_cosine_similarity(query_embedding, entity_embedding)
            if similarity >= similarity_threshold:
                results.append({
                    'id': row['id'],
                    'name': row['name'],
                    'type': row['type'],
                    'similarity': similarity
                })
    return results

def get_entity_by_embedding(
    text: str, 
    similarity_threshold: float = 0.7, 
    use_parallel: bool = True,
    max_workers: int = 4,
    use_cache: bool = True
) -> List[Dict[str, Any]]:
    """Find entities in the database similar to the given text using embeddings.
    
    Args:
        text: Text to search for
        similarity_threshold: Minimum similarity score to include (default: 0.7)
        use_parallel: Whether to use parallel processing (default: True)
        max_workers: Maximum number of worker threads for parallel processing (default: 4)
        use_cache: Whether to use the embedding cache (default: True)
        
    Returns:
        List of entity records with similarity >= similarity_threshold
    """
    try:
        # Get database connection
        con = get_sqlite()
        
        # Ensure row factory is set to return dictionaries
        con.row_factory = sqlite3.Row
        
        # Get embedding for the text
        query_embedding = embed_texts(text, use_cache=use_cache)        # Try to use native vector search if available
        try:
            # Check if sqlite_vec extension is loaded and working
            cursor = con.cursor()
            cursor.execute("SELECT vec_version()")
            version = cursor.fetchone()
            
            if version:
                _logger.debug(f"Using sqlite-vec native vector search (version: {version[0]})")
                
                # Check if entity_vectors table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='entity_vectors'")
                vectors_table_exists = cursor.fetchone() is not None
                
                if vectors_table_exists:
                    # Convert query embedding to proper format
                    import sqlite_vec
                    query_vector = sqlite_vec.serialize_float32(extract_vector(query_embedding))
                      # Use native vector search with the virtual table
                    sql_text = """
                    SELECT e.id, e.name, e.type, e.embedding, 
                           vec_distance_cosine(v.embedding, ?) as distance
                    FROM entity_vectors v
                    JOIN entity e ON e.id = v.entity_id
                    WHERE v.embedding MATCH ?
                      AND k = 50
                    ORDER BY distance
                    """
                    
                    # For sqlite-vec, we need to pass the query vector twice
                    cursor.execute(sql_text, (query_vector, query_vector))
                    rows = cursor.fetchall()
                    
                    # Convert to the expected format
                    results = []
                    for row in rows:
                        # Convert cosine distance to similarity
                        similarity = 1.0 - row[4]
                        if similarity >= similarity_threshold:
                            result = {
                                'id': row[0],
                                'name': row[1], 
                                'type': row[2],
                                'embedding': row[3],
                                'similarity': similarity
                            }
                            results.append(result)
                    
                    _logger.debug(f"sqlite-vec returned {len(results)} results")
                    return results
                else:
                    _logger.warning("entity_vectors table not found, falling back to manual similarity")
        except Exception as e:
            _logger.warning(f"Native vector search failed, falling back to manual similarity: {e}")
        
        # Fallback to manual similarity calculation
        _logger.debug("Using manual similarity calculation")
        
        # Fetch all entities with embeddings
        cursor = con.execute("SELECT id, name, type, embedding FROM entity WHERE embedding IS NOT NULL")
        rows = cursor.fetchall()
        
        if not rows:
            return []
            
        # Use parallel processing for better performance if enabled
        if use_parallel and len(rows) > 10:
            # Split data into batches for parallel processing
            batch_size = max(10, len(rows) // max_workers)
            batches = [rows[i:i + batch_size] for i in range(0, len(rows), batch_size)]
            
            _logger.debug(f"Processing {len(rows)} entities in {len(batches)} batches")
            
            # Create partial function with fixed parameters
            process_func = partial(_process_entity_batch, 
                                   query_embedding=query_embedding, 
                                   similarity_threshold=similarity_threshold)
            
            # Process batches in parallel
            results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                batch_results = executor.map(process_func, batches)
                for batch_result in batch_results:
                    results.extend(batch_result)
        else:
            # Sequential processing for small datasets
            results = _process_entity_batch(rows, query_embedding, similarity_threshold)
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results
        
    except Exception as e:
        _logger.error(f"Error in get_entity_by_embedding: {e}")
        return []

def get_entity_by_text(text: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Find entities in the database by text matching.
    
    This is a fallback for when vector search is not available.
    
    Args:
        text: Text to search for
        limit: Maximum number of results to return
        
    Returns:
        List of entity records matching the text
    """
    try:
        # Get database connection
        con = get_sqlite()
        
        # Ensure row factory is set to return dictionaries
        con.row_factory = sqlite3.Row
        
        # Use LIKE with word boundaries to find matches
        sql_text = """
        SELECT id, name, type 
        FROM entity 
        WHERE LOWER(name) LIKE ? OR LOWER(name) LIKE ? OR LOWER(name) = ? OR LOWER(name) LIKE ?
        ORDER BY 
            CASE 
                WHEN LOWER(name) = ? THEN 1
                WHEN LOWER(name) LIKE ? THEN 2
                WHEN LOWER(name) LIKE ? THEN 3
                ELSE 4
            END
        LIMIT ?
        """
        
        # Add wildcards for partial matching with case insensitive search
        params = (
            f"% {text.lower()} %",  # Word in the middle
            f"{text.lower()} %",    # Word at the beginning
            text.lower(),           # Exact match
            f"%{text.lower()}%",    # Substring match
            text.lower(),           # For ordering: exact match first
            f"{text.lower()} %",    # For ordering: word at beginning second
            f"% {text.lower()} %",  # For ordering: word in middle third
            limit
        )
        
        cursor = con.execute(sql_text, params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
        
    except Exception as e:
        _logger.error(f"Error in get_entity_by_text: {e}")
        return []

def get_entities_by_embeddings(
    texts: List[str], 
    similarity_threshold: float = 0.7,
    use_parallel: bool = True,
    max_workers: int = 4,
    use_cache: bool = True
) -> Dict[str, List[Dict[str, Any]]]:
    """Find entities in the database similar to multiple texts using embeddings.
    
    Args:
        texts: List of texts to search for
        similarity_threshold: Minimum similarity score to include (default: 0.7)
        use_parallel: Whether to use parallel processing (default: True)
        max_workers: Maximum number of worker threads for parallel processing (default: 4)
        use_cache: Whether to use the embedding cache (default: True)
        
    Returns:
        Dictionary mapping input texts to their matching entities
    """
    results = {}
    
    # Process each text
    if use_parallel and len(texts) > 5:
        # Define function to process a single text
        def process_single_text(text):
            return text, get_entity_by_embedding(
                text, 
                similarity_threshold=similarity_threshold,
                use_parallel=False,  # Already using parallel at this level
                use_cache=use_cache
            )
        
        # Process texts in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            for text, entities in executor.map(process_single_text, texts):
                results[text] = entities
    else:
        # Sequential processing
        for text in texts:
            results[text] = get_entity_by_embedding(
                text, 
                similarity_threshold=similarity_threshold,
                use_parallel=use_parallel,
                max_workers=max_workers,
                use_cache=use_cache
            )
    
    return results

def batch_store_embeddings(entities_data: List[Dict[str, Any]], use_cache: bool = True) -> int:
    """Store embeddings for multiple entities in batch.
    
    Args:
        entities_data: List of entity dictionaries with 'name' and optionally 'type', 'source_doc'
        use_cache: Whether to use the embedding cache (default: True)
        
    Returns:
        Number of entities successfully processed
    """
    if not entities_data:
        return 0
        
    try:
        # Get database connection
        con = get_sqlite()
        
        # Extract texts for batch embedding
        texts = [entity['name'] for entity in entities_data]
        
        # Get embeddings for all texts at once
        embeddings = embed_texts(texts, use_cache=use_cache)
        
        # Prepare data for batch insert/update
        processed_count = 0
        for i, entity in enumerate(entities_data):
            try:                # Get the embedding for this entity
                entity_embedding = None
                if isinstance(embeddings, list) and len(embeddings) > i:
                    if isinstance(embeddings[i], list):
                        entity_embedding = embeddings[i]
                    else:
                        # Handle case where embeddings is a single embedding
                        if isinstance(embeddings, list):
                            entity_embedding = embeddings
                else:
                    continue
                
                # Ensure we have a valid embedding and it's a list
                if entity_embedding is None or not isinstance(entity_embedding, list):
                    continue
                
                # Convert embedding to binary
                embedding_binary = embedding_to_binary(entity_embedding)
                
                # Update or insert entity with embedding
                cursor = con.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO entity (name, type, source_doc, embedding)
                    VALUES (?, ?, ?, ?)
                """, (
                    entity['name'],
                    entity.get('type', ''),
                    entity.get('source_doc', ''),
                    embedding_binary
                ))
                
                # Get the entity ID
                entity_id = cursor.lastrowid
                if entity_id and isinstance(entity_embedding, list):
                    # Sync to vector table if available
                    sync_entity_to_vector_table(entity_id, entity_embedding)
                
                processed_count += 1
                
            except Exception as e:
                _logger.warning(f"Error processing entity {entity.get('name', 'unknown')}: {e}")
                continue
        
        # Commit all changes
        con.commit()
        
        _logger.info(f"Successfully processed embeddings for {processed_count}/{len(entities_data)} entities")
        return processed_count
        
    except Exception as e:
        _logger.error(f"Error in batch_store_embeddings: {e}")
        return 0

def sync_entity_to_vector_table(entity_id: int, embedding: Union[List[float], List[List[float]]]) -> bool:
    """Sync an entity's embedding to the sqlite-vec virtual table.
    
    Args:
        entity_id: The entity ID
        embedding: The embedding vector
        
    Returns:
        True if successful, False otherwise
    """
    if sqlite_vec is None:
        return False
        
    try:
        con = get_sqlite()
        cursor = con.cursor()
        
        # Check if entity_vectors table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='entity_vectors'")
        if not cursor.fetchone():
            return False
            
        # Convert embedding to proper format
        vector = extract_vector(embedding)
        vector_data = sqlite_vec.serialize_float32(vector)
        
        # Insert or replace the vector
        cursor.execute("""
            INSERT OR REPLACE INTO entity_vectors (entity_id, embedding)
            VALUES (?, ?)
        """, (entity_id, vector_data))
        
        con.commit()
        return True
        
    except Exception as e:
        _logger.error(f"Error syncing entity {entity_id} to vector table: {e}")
        return False

def batch_sync_entities_to_vector_table() -> int:
    """Sync all entities with embeddings to the sqlite-vec virtual table.
    
    Returns:
        Number of entities successfully synced
    """
    if sqlite_vec is None:
        _logger.warning("sqlite_vec not available for batch sync")
        return 0
        
    try:
        con = get_sqlite()
        cursor = con.cursor()
        
        # Check if entity_vectors table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='entity_vectors'")
        if not cursor.fetchone():
            _logger.warning("entity_vectors table not found")
            return 0
            
        # Get all entities with embeddings
        cursor.execute("SELECT id, embedding FROM entity WHERE embedding IS NOT NULL")
        entities = cursor.fetchall()
        
        if not entities:
            _logger.info("No entities with embeddings found")
            return 0
            
        synced_count = 0
        for entity_id, embedding_blob in entities:
            try:
                # Convert binary embedding back to vector
                if embedding_blob:
                    embedding = binary_to_embedding(embedding_blob)
                    if embedding and sync_entity_to_vector_table(entity_id, embedding):
                        synced_count += 1
            except Exception as e:
                _logger.warning(f"Error syncing entity {entity_id}: {e}")
                continue
                
        _logger.info(f"Synced {synced_count}/{len(entities)} entities to vector table")
        return synced_count
        
    except Exception as e:
        _logger.error(f"Error in batch sync: {e}")
        return 0
