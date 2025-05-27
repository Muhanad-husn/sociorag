"""Reset helper for SocioGraph.

This module provides functions to reset the corpus state by clearing the vector store,
input directory, saved directory, and graph database.
"""

import shutil
import sqlite3
from pathlib import Path

from backend.app.core.config import get_config
from backend.app.core.singletons import SQLiteSingleton


def reset_corpus():
    """Reset the corpus by clearing all data stores.
    
    This function:
    1. Removes and recreates the vector store directory
    2. Removes and recreates the input directory
    3. Removes and recreates the saved directory
    4. Clears the graph database content
    """
    cfg = get_config()
    
    # Clear directories
    for path in [cfg.VECTOR_DIR, cfg.INPUT_DIR, cfg.SAVED_DIR]:
        shutil.rmtree(path, ignore_errors=True)
        path.mkdir(exist_ok=True)
    
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
        
        return {"status": "corpus cleared"}
        
    except Exception as e:
        # If database operations fail, try the file deletion approach
        # but only as a fallback
        try:
            Path(cfg.GRAPH_DB).unlink(missing_ok=True)
            return {"status": "corpus cleared (database recreated)"}
        except Exception as file_e:
            raise Exception(f"Failed to clear database: {e}, and failed to delete file: {file_e}")
    
    return {"status": "corpus cleared"}
    
    return {"status": "corpus cleared"}