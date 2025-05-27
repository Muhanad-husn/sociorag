#!/usr/bin/env python3
"""
Initialize database schema for SocioGraph.

This script creates the required database tables if they don't exist.
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.core.singletons import SQLiteSingleton, get_logger

logger = get_logger()

def create_documents_table():
    """Create the documents table if it doesn't exist."""
    try:
        db_conn = SQLiteSingleton().get()
        cursor = db_conn.cursor()
        
        # Create documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                upload_time TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                status TEXT DEFAULT 'uploaded',
                metadata TEXT,
                processing_stats TEXT
            )
        """)
        
        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_status ON documents (status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_upload_time ON documents (upload_time)
        """)
        
        db_conn.commit()
        cursor.close()
        
        logger.info("✅ Documents table created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create documents table: {e}")
        return False

def create_chunks_table():
    """Create the chunks table for vector storage."""
    try:
        db_conn = SQLiteSingleton().get()
        cursor = db_conn.cursor()
        
        # Create chunks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                embedding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(document_id)
            )
        """)
        
        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks (document_id)
        """)
        
        db_conn.commit()
        cursor.close()
        
        logger.info("✅ Chunks table created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create chunks table: {e}")
        return False

def verify_existing_tables():
    """Verify existing tables are correct."""
    try:
        db_conn = SQLiteSingleton().get()
        cursor = db_conn.cursor()
        
        # Check entity table
        cursor.execute("SELECT COUNT(*) FROM entity")
        entity_count = cursor.fetchone()[0]
        logger.info(f"Entity table: {entity_count} entities")
        
        # Check relation table  
        cursor.execute("SELECT COUNT(*) FROM relation")
        relation_count = cursor.fetchone()[0]
        logger.info(f"Relation table: {relation_count} relations")
        
        # Check documents table
        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]
        logger.info(f"Documents table: {doc_count} documents")
        
        cursor.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to verify tables: {e}")
        return False

def main():
    """Main initialization function."""
    logger.info("Initializing SocioGraph database schema...")
    
    success = True
    
    # Create documents table
    if not create_documents_table():
        success = False
    
    # Create chunks table
    if not create_chunks_table():
        success = False
    
    # Verify all tables
    if not verify_existing_tables():
        success = False
    
    if success:
        logger.info("🎉 Database schema initialization completed successfully!")
        return True
    else:
        logger.error("💥 Database schema initialization failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
