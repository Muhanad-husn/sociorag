"""Reset helper for SocioGraph.

This module provides functions to reset the corpus state by clearing the vector store,
input directory, saved directory, graph database, and embedding cache.
"""

import shutil
import sqlite3
from pathlib import Path

from ..core.config import get_config
from ..core.singletons import SQLiteSingleton, ChromaSingleton, LoggerSingleton
from ..retriever.embedding_cache import get_embedding_cache


def reset_corpus():
    """Reset the corpus by clearing all data stores.
    
    This function:
    1. Removes and recreates the vector store directory
    2. Removes and recreates the input directory
    3. Removes and recreates the saved directory
    4. Clears the graph database content
    5. Clears the embedding cache
    """
    cfg = get_config()
    logger = LoggerSingleton().get()
    
    # Clear the embedding cache
    try:
        cache = get_embedding_cache()
        cache_size = cache.size()
        cache.clear()
        logger.info(f"Cleared embedding cache ({cache_size} entries)")
    except Exception as e:
        logger.warning(f"Failed to clear embedding cache: {e}")
    
    # Get ChromaDB instance and delete all documents in the collection
    try:
        # First try to delete documents using the API
        chroma_singleton = ChromaSingleton()
        if chroma_singleton._chroma is not None:
            collection = chroma_singleton._chroma._collection
            # Get all IDs in the collection
            all_ids = collection.get()["ids"]
            if all_ids:
                # Delete all documents by ID
                collection.delete(all_ids)
    except Exception as e:
        # If API deletion fails, fall back to directory removal
        pass
        
    # Clear directories
    for path in [cfg.VECTOR_DIR, cfg.INPUT_DIR, cfg.SAVED_DIR]:
        shutil.rmtree(path, ignore_errors=True)
        path.mkdir(exist_ok=True)
    
    # Reset the ChromaSingleton's stored instance
    # to ensure it reconnects to the now-empty vector store
    chroma_singleton = ChromaSingleton()
    chroma_singleton._chroma = None
    
    # Clear database content instead of deleting the file
    try:
        # Get the SQLite connection from the singleton
        db_conn = SQLiteSingleton().get()
        cursor = db_conn.cursor()
        
        # Clear all tables instead of deleting the file
        # Get list of user tables (exclude system tables)
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND name NOT LIKE 'sqlite_%'
        """)
        tables = cursor.fetchall()
        
        # Clear each table
        for table in tables:
            table_name = table[0]
            cursor.execute(f"DELETE FROM {table_name}")
          # Commit the changes
        db_conn.commit()
        cursor.close()
        
        logger.info("Corpus reset completed successfully")
        return {"success": True, "message": "Corpus reset successfully"}
        
    except Exception as e:
        # If database operations fail, try the file deletion approach
        # but only as a fallback
        try:
            Path(cfg.GRAPH_DB).unlink(missing_ok=True)
            logger.info("Corpus reset completed (database recreated)")
            return {"success": True, "message": "Corpus reset successfully (database recreated)"}
        except Exception as file_e:
            logger.error(f"Failed to clear database: {e}, and failed to delete file: {file_e}")
            raise Exception(f"Failed to clear database: {e}, and failed to delete file: {file_e}")
    
    logger.info("Corpus reset completed successfully")
    return {"success": True, "message": "Corpus reset successfully"}