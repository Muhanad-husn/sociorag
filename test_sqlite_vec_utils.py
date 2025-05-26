"""
Test SQLite vector utilities for SocioGraph.

This script tests the SQLite vector utilities module to ensure it correctly
handles embedding conversions and entity searches.
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import the app modules
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.core.singletons import get_logger, get_sqlite, embed_texts
from backend.app.retriever.sqlite_vec_utils import (
    embedding_to_binary,
    binary_to_embedding,
    get_entity_by_embedding,
    get_entity_by_text
)

# Initialize logger
logger = get_logger()

def test_embedding_conversion():
    """Test conversion between embeddings and binary blobs."""
    logger.info("Testing embedding conversion functions...")
    
    # Generate a test embedding
    test_text = "This is a test of embedding conversion"
    embedding = embed_texts(test_text)
    
    # Convert to binary
    binary_data = embedding_to_binary(embedding)
    logger.info(f"Converted embedding to binary: {len(binary_data)} bytes")
    
    # Convert back to embedding
    recovered_embedding = binary_to_embedding(binary_data)
    logger.info(f"Recovered embedding with {len(recovered_embedding)} dimensions")
    
    # Check if the conversion was lossless
    # Compare first 5 values
    logger.info(f"Original first 5 values: {embedding[:5]}")
    logger.info(f"Recovered first 5 values: {recovered_embedding[:5]}")
    
    # Check if dimensions match
    assert len(embedding) == len(recovered_embedding), "Embedding dimensions don't match"
    
    # Check if values are close (may have small floating point differences)
    diffs = [abs(a - b) for a, b in zip(embedding, recovered_embedding)]
    max_diff = max(diffs)
    logger.info(f"Maximum difference between original and recovered: {max_diff}")
    assert max_diff < 1e-6, "Embedding values don't match"
    
    logger.info("Embedding conversion test passed!")

def test_entity_search():
    """Test entity search functions."""
    logger.info("Testing entity search functions...")
    
    # Try text-based search first
    test_term = "climate"
    text_results = get_entity_by_text(test_term)
    logger.info(f"Text search for '{test_term}' returned {len(text_results)} results:")
    for i, entity in enumerate(text_results[:5]):  # Show top 5
        logger.info(f"  {i+1}. {entity['name']} ({entity['type']})")
    
    # Try embedding-based search
    embedding_results = get_entity_by_embedding(test_term)
    logger.info(f"Embedding search for '{test_term}' returned {len(embedding_results)} results:")
    for i, entity in enumerate(embedding_results[:5]):  # Show top 5
        logger.info(f"  {i+1}. {entity['name']} ({entity['type']}) - similarity: {entity['similarity']:.4f}")

if __name__ == "__main__":
    logger.info("Starting SQLite vector utilities test...")
    
    # Test embedding conversion
    test_embedding_conversion()
    
    # Test entity search
    test_entity_search()
    
    logger.info("SQLite vector utilities tests completed successfully!")
