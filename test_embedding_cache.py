"""
Test embedding cache functionality for SocioGraph.

This script tests the embedding cache module to verify that it correctly
caches embeddings and improves performance.
"""

import sys
import time
from pathlib import Path

# Add the parent directory to the path so we can import the app modules
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.core.singletons import get_logger, embed_texts
from backend.app.retriever.embedding_cache import get_embedding_cache

# Initialize logger
logger = get_logger()

def test_cache_hit():
    """Test that embeddings are correctly cached and retrieved."""
    logger.info("Testing embedding cache hits...")
    
    # Get the cache
    cache = get_embedding_cache()
    
    # Clear the cache to start with a clean state
    cache.clear()
    logger.info(f"Cleared cache, current size: {cache.size()}")
    
    # Test text to embed
    test_text = "This is a test of the embedding cache functionality"
    
    # First embedding (should be a cache miss)
    start_time = time.time()
    first_embedding = embed_texts(test_text)
    first_time = time.time() - start_time
    logger.info(f"First embedding took {first_time:.4f}s (cache miss)")
    
    # Second embedding of the same text (should be a cache hit)
    start_time = time.time()
    second_embedding = embed_texts(test_text)
    second_time = time.time() - start_time
    logger.info(f"Second embedding took {second_time:.4f}s (cache hit)")
    
    # Verify the embeddings are the same
    assert first_embedding == second_embedding, "Cached embedding doesn't match original"
    
    # Verify the cache hit was faster
    assert second_time < first_time, "Cache hit should be faster than miss"
    logger.info(f"Cache hit was {first_time/second_time:.1f}x faster than miss")
    
    # Check cache size
    logger.info(f"Cache size after test: {cache.size()}")
    
    return first_time, second_time

def test_cache_batch():
    """Test that batch embeddings are correctly cached."""
    logger.info("Testing batch embedding cache...")
    
    # Get the cache
    cache = get_embedding_cache()
    
    # Test texts to embed
    test_texts = [
        "The quick brown fox jumps over the lazy dog",
        "Lorem ipsum dolor sit amet",
        "Machine learning is a subset of artificial intelligence"
    ]
    
    # First batch embedding (should be a cache miss)
    start_time = time.time()
    first_embeddings = embed_texts(test_texts)
    first_time = time.time() - start_time
    logger.info(f"First batch embedding took {first_time:.4f}s (cache miss)")
    
    # Second batch embedding of the same texts (should be a cache hit)
    start_time = time.time()
    second_embeddings = embed_texts(test_texts)
    second_time = time.time() - start_time
    logger.info(f"Second batch embedding took {second_time:.4f}s (cache hit)")
    
    # Verify the embeddings are the same
    assert first_embeddings == second_embeddings, "Cached batch embeddings don't match original"
    
    # Verify the cache hit was faster
    assert second_time < first_time, "Cache hit should be faster than miss"
    logger.info(f"Batch cache hit was {first_time/second_time:.1f}x faster than miss")
    
    return first_time, second_time

def test_cache_expiration():
    """Test that cache entries expire after TTL."""
    logger.info("Testing cache expiration...")
    
    # Get the cache with a very short TTL for testing
    from backend.app.retriever.embedding_cache import EmbeddingCache
    test_cache = EmbeddingCache(ttl_seconds=2)
    
    # Test text to embed
    test_text = "This is a test of cache expiration"
    
    # Store a dummy embedding in the cache
    dummy_embedding = [0.1, 0.2, 0.3]
    test_cache.set(test_text, dummy_embedding)
    
    # Verify it's in the cache
    cached = test_cache.get(test_text)
    assert cached == dummy_embedding, "Embedding should be in cache"
    logger.info("Embedding successfully stored in cache")
    
    # Wait for expiration
    logger.info("Waiting for cache entry to expire...")
    time.sleep(3)
    
    # Verify it's expired
    cached = test_cache.get(test_text)
    assert cached is None, "Embedding should have expired"
    logger.info("Embedding successfully expired from cache")
    
def test_cache_cleanup():
    """Test that cleanup removes expired entries."""
    logger.info("Testing cache cleanup...")
    
    # Get the cache with a very short TTL for testing
    from backend.app.retriever.embedding_cache import EmbeddingCache
    test_cache = EmbeddingCache(ttl_seconds=1)
    
    # Add several test entries
    for i in range(5):
        test_cache.set(f"test{i}", [float(i)])
        
    # Verify all entries are in the cache
    assert test_cache.size() == 5, "Cache should have 5 entries"
    logger.info(f"Added 5 entries to cache, current size: {test_cache.size()}")
    
    # Wait for expiration
    logger.info("Waiting for cache entries to expire...")
    time.sleep(2)
    
    # Run cleanup
    removed = test_cache.cleanup()
    logger.info(f"Cleanup removed {removed} expired entries")
    
    # Verify entries were removed
    assert test_cache.size() == 0, "Cache should be empty after cleanup"
    logger.info(f"Cache size after cleanup: {test_cache.size()}")

if __name__ == "__main__":
    logger.info("Starting embedding cache test...")
    
    # Test cache hit
    miss_time, hit_time = test_cache_hit()
    
    # Test batch cache
    batch_miss_time, batch_hit_time = test_cache_batch()
    
    # Test cache expiration
    test_cache_expiration()
    
    # Test cache cleanup
    test_cache_cleanup()
    
    # Summary
    logger.info("\nEmbedding Cache Performance Summary:")
    logger.info(f"Single text cache hit: {miss_time/hit_time:.1f}x speedup")
    logger.info(f"Batch texts cache hit: {batch_miss_time/batch_hit_time:.1f}x speedup")
    
    logger.info("Embedding cache test completed successfully!")
