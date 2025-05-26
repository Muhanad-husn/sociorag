"""
Simple verification script to ensure system functionality after Phase 4 cleanup.

This script performs basic operations to verify that the core functionality
of SocioGraph remains intact after cleanup.
"""

import sys
import time
from pathlib import Path

# Add the project root to the path so we can import modules
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.app.core.singletons import get_logger, embed_texts
from backend.app.retriever import retrieve_context

def verify_embedding():
    """Verify embedding functionality with caching."""
    logger = get_logger()
    
    # Test text for embedding
    test_text = "This is a test of the embedding functionality after cleanup."
    
    # First embedding (may be a cache miss)
    start_time = time.time()
    embedding1 = embed_texts([test_text])
    first_time = time.time() - start_time
    
    # Second embedding (should be a cache hit)
    start_time = time.time()
    embedding2 = embed_texts([test_text])
    second_time = time.time() - start_time
    
    # Verification
    logger.info(f"First embedding time: {first_time:.4f}s")
    logger.info(f"Second embedding time: {second_time:.4f}s")
    logger.info(f"Cache speedup: {first_time/second_time:.2f}x")
    
    # Basic validation
    assert len(embedding1) == 1, "Embedding should return a list with one item"
    assert len(embedding1[0]) > 0, "Embedding vector should have non-zero length"
    
    return first_time > second_time

def verify_retrieval():
    """Verify context retrieval functionality."""
    logger = get_logger()
    
    # Test query
    test_query = "What are the effects of climate change?"
    
    # Retrieve context
    start_time = time.time()
    context = retrieve_context(test_query)
    retrieval_time = time.time() - start_time
    
    # Verification
    logger.info(f"Context retrieval time: {retrieval_time:.4f}s")
    logger.info(f"Retrieved {len(context)} context items")
    
    # Basic validation
    assert context is not None, "Context should not be None"
    
    return len(context) > 0

def main():
    """Run verification checks."""
    logger = get_logger()
    logger.info("Starting post-cleanup verification")
    
    # Run verification checks
    embedding_ok = verify_embedding()
    retrieval_ok = verify_retrieval()
    
    # Report results
    logger.info(f"Embedding verification: {'PASSED' if embedding_ok else 'FAILED'}")
    logger.info(f"Retrieval verification: {'PASSED' if retrieval_ok else 'FAILED'}")
    
    if embedding_ok and retrieval_ok:
        logger.info("✅ All verifications PASSED - system is functioning correctly after cleanup")
        return 0
    else:
        logger.error("❌ Verification FAILED - system may be compromised by cleanup")
        return 1

if __name__ == "__main__":
    sys.exit(main())
