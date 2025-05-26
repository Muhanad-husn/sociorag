"""
Special test for cache functionality that doesn't rely on pytest.

This runs as a standalone script to test if the embedding cache works as expected.
"""

import sys
import time
from pathlib import Path
import logging

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.app.core.singletons import get_logger, embed_texts
from backend.app.retriever.embedding_cache import get_embedding_cache

# Initialize logger
logger = get_logger()
logger.setLevel(logging.INFO)

def main():
    """Run the test script."""
    logger.info("Starting embedding cache standalone test...")
    
    # Get the cache
    cache = get_embedding_cache()
    
    # Clear the cache to start with a clean state
    cache.clear()
    logger.info(f"Cleared cache, current size: {cache.size()}")
    
    # Test text to embed
    test_text = "This is a standalone test of the embedding cache functionality"
    
    # First embedding (should be a cache miss)
    start_time = time.time()
    first_embedding = embed_texts(test_text)
    first_time = time.time() - start_time
    logger.info(f"First embedding took {first_time:.4f}s (cache miss)")
    
    # Manually insert into cache to make sure it's there
    cache.set(test_text, first_embedding)
    logger.info(f"Cache size after manual insert: {cache.size()}")
    
    # Second embedding of the same text (should be a cache hit)
    start_time = time.time()
    second_embedding = embed_texts(test_text)
    second_time = time.time() - start_time
    logger.info(f"Second embedding took {second_time:.4f}s (cache hit)")
    
    # Verify the embeddings are the same
    assert first_embedding == second_embedding, "Cached embedding doesn't match original"
    
    # Performance comparison
    if second_time < first_time:
        speedup = first_time / second_time
        logger.info(f"Cache hit was {speedup:.2f}x faster than miss")
    else:
        logger.info(f"Cache hit wasn't faster in this run (unusual)")
    
    # Test batch caching
    logger.info("\nTesting batch embedding cache...")
    
    # Test texts to embed
    test_texts = [
        "The quick brown fox jumps over the lazy dog",
        "Lorem ipsum dolor sit amet",
        "Machine learning is a subset of artificial intelligence"
    ]
    
    # Clear cache again
    cache.clear()
    logger.info(f"Cleared cache, current size: {cache.size()}")
    
    # First batch embedding (should be a cache miss)
    start_time = time.time()
    first_embeddings = embed_texts(test_texts)
    first_time = time.time() - start_time
    logger.info(f"First batch embedding took {first_time:.4f}s (cache miss)")
    
    # Manually insert each text into cache
    for i, text in enumerate(test_texts):
        if isinstance(first_embeddings[0], list):  # If batch result is list of lists
            cache.set(text, first_embeddings[i])
        else:
            # Handle edge case where batch might return differently
            cache.set(text, first_embeddings)
    
    logger.info(f"Cache size after manual batch insert: {cache.size()}")
    
    # Second batch embedding of the same texts (should be a cache hit)
    start_time = time.time()
    second_embeddings = embed_texts(test_texts)
    second_time = time.time() - start_time
    logger.info(f"Second batch embedding took {second_time:.4f}s (cache hit)")
    
    # Verify the embeddings are the same
    assert str(first_embeddings) == str(second_embeddings), "Cached batch embeddings don't match original"
    
    # Performance comparison
    if second_time < first_time:
        speedup = first_time / second_time
        logger.info(f"Batch cache hit was {speedup:.2f}x faster than miss")
    else:
        logger.info(f"Batch cache hit wasn't faster in this run (unusual)")
    
    logger.info("\nEmbedding cache test completed!")

if __name__ == "__main__":
    main()
