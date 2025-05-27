#!/usr/bin/env python3
"""
Check ChromaDB vector store status and initialize if needed.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.core.singletons import get_chroma, get_logger

logger = get_logger()

def check_vector_store():
    """Check the status of the ChromaDB vector store."""
    try:
        # Get ChromaDB instance
        vectordb = get_chroma()
        logger.info("✅ Successfully connected to ChromaDB")
        
        # Get the collection
        collection = vectordb._collection
        logger.info(f"Collection name: {collection.name}")
        
        # Check the number of documents
        count = collection.count()
        logger.info(f"Number of documents in collection: {count}")
        
        # Get a peek at the data if any exists
        if count > 0:
            # Get first 5 documents as a sample
            results = collection.peek(limit=5)
            logger.info(f"Sample documents:")
            for i, (doc_id, metadata) in enumerate(zip(results['ids'], results['metadatas'])):
                logger.info(f"  {i+1}. ID: {doc_id}, Metadata: {metadata}")
        else:
            logger.warning("⚠️  Vector store is empty - no documents found")
            
        return count > 0
        
    except Exception as e:
        logger.error(f"❌ Failed to check vector store: {e}")
        return False

def initialize_vector_store():
    """Initialize the vector store if needed."""
    try:
        # Test basic functionality
        vectordb = get_chroma()
        
        # Try a simple similarity search to test the setup
        test_results = vectordb.similarity_search("test query", k=1)
        logger.info(f"Test search returned {len(test_results)} results")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize vector store: {e}")
        return False

def main():
    """Main function."""
    logger.info("Checking ChromaDB vector store status...")
    
    # Check if vector store has data
    has_data = check_vector_store()
    
    if not has_data:
        logger.info("Vector store is empty. This is expected if no documents have been processed yet.")
        
        # Test basic functionality
        if initialize_vector_store():
            logger.info("✅ Vector store is properly initialized and ready for document ingestion")
            return True
        else:
            logger.error("❌ Vector store initialization failed")
            return False
    else:
        logger.info("✅ Vector store has data and appears to be working correctly")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
