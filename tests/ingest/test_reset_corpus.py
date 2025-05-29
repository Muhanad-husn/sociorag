#!/usr/bin/env python3
"""
Test script for the reset_corpus functionality.

This script tests that the reset_corpus function properly clears both
the vector store and SQLite database by checking record counts before and after.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from backend.app.core.singletons import get_logger, get_chroma, SQLiteSingleton, ChromaSingleton, embed_texts
from backend.app.ingest.reset import reset_corpus
from backend.app.retriever.embedding_cache import get_embedding_cache

# Initialize logger
logger = get_logger()

def count_vector_store_records():
    """Count the number of records in the vector store."""
    try:
        # Get ChromaDB instance
        vectordb = get_chroma()
        
        # Get the collection
        collection = vectordb._collection
        
        # Check the number of documents
        count = collection.count()
        logger.info(f"Vector store document count: {count}")
        
        return count
        
    except Exception as e:
        logger.error(f"Failed to count vector store records: {e}")
        return -1

def count_sqlite_records():
    """Count records in the SQLite database tables."""
    try:
        # Get SQLite connection
        db_conn = SQLiteSingleton().get()
        cursor = db_conn.cursor()
        
        # Get list of user tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND name NOT LIKE 'sqlite_%'
        """)
        tables = cursor.fetchall()
        
        # Count records in each table
        table_counts = {}
        total_count = 0
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            table_counts[table_name] = count
            total_count += count
            logger.info(f"Table '{table_name}' record count: {count}")
        
        cursor.close()
        
        return total_count, table_counts
        
    except Exception as e:
        logger.error(f"Failed to count SQLite records: {e}")
        return -1, {}

def count_embedding_cache_entries():
    """Count the number of entries in the embedding cache."""
    try:
        # Get embedding cache
        cache = get_embedding_cache()
        
        # Get the number of entries
        count = cache.size()
        logger.info(f"Embedding cache entry count: {count}")
        
        return count
        
    except Exception as e:
        logger.error(f"Failed to count embedding cache entries: {e}")
        return -1

def test_reset_corpus():
    """Test the reset_corpus function."""
    logger.info("=== Testing reset_corpus functionality ===")
    
    # Add some test data to the embedding cache
    logger.info("Adding test data to embedding cache...")
    test_text = "This is a test text for the embedding cache"
    cache = get_embedding_cache()
    cache.clear()  # Start with a clean cache
    
    # Manually add an entry to the cache to ensure we have something to clear
    dummy_embedding = [0.1, 0.2, 0.3]
    cache.set(test_text, dummy_embedding)
    logger.info(f"Manually added test entry to embedding cache")
    
    # Count records before reset
    logger.info("Counting records before reset...")
    vector_count_before = count_vector_store_records()
    sqlite_count_before, sqlite_tables_before = count_sqlite_records()
    embedding_cache_count_before = count_embedding_cache_entries()
    
    logger.info(f"Before reset: Vector store has {vector_count_before} documents")
    logger.info(f"Before reset: SQLite has {sqlite_count_before} total records")
    logger.info(f"Before reset: Embedding cache has {embedding_cache_count_before} entries")
    
    # Execute reset_corpus
    logger.info("Executing reset_corpus...")
    result = reset_corpus()
    logger.info(f"Reset result: {result}")
    
    # Count records after reset - force a new instance of ChromaDB
    logger.info("Counting records after reset...")
    
    # Force a completely new ChromaDB instance
    # This is necessary to ensure we're not using a cached instance
    chroma_singleton = ChromaSingleton()
    if hasattr(chroma_singleton, '_chroma') and chroma_singleton._chroma is not None:
        logger.info("ChromaSingleton still has an instance, forcing it to None")
        chroma_singleton._chroma = None
        
    # Use the get_chroma() function to get a fresh instance
    vector_count_after = count_vector_store_records()
    sqlite_count_after, sqlite_tables_after = count_sqlite_records()
    embedding_cache_count_after = count_embedding_cache_entries()
    
    logger.info(f"After reset: Vector store has {vector_count_after} documents")
    logger.info(f"After reset: SQLite has {sqlite_count_after} total records")
    logger.info(f"After reset: Embedding cache has {embedding_cache_count_after} entries")
    
    # Verify reset was successful
    vector_reset_success = vector_count_after == 0
    if vector_reset_success:
        logger.info("Vector store was successfully reset (0 documents)")
    else:
        logger.error(f"Vector store reset failed, {vector_count_after} documents remain")
    
    sqlite_reset_success = sqlite_count_after == 0
    if sqlite_reset_success:
        logger.info("SQLite database was successfully reset (0 records)")
    else:
        logger.error(f"SQLite database reset failed, {sqlite_count_after} records remain")
        logger.error("Remaining records by table:")
        for table_name, count in sqlite_tables_after.items():
            if count > 0:
                logger.error(f"  - Table '{table_name}': {count} records")
    
    embedding_cache_reset_success = embedding_cache_count_after == 0
    if embedding_cache_reset_success:
        logger.info("Embedding cache was successfully reset (0 entries)")
    else:
        logger.error(f"Embedding cache reset failed, {embedding_cache_count_after} entries remain")
    
    # Return overall success status
    return vector_reset_success and sqlite_reset_success and embedding_cache_reset_success

if __name__ == "__main__":
    success = test_reset_corpus()
    logger.info("=== Test complete ===")
    sys.exit(0 if success else 1)
