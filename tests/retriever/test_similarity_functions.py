"""
Test script to verify that the centralized cosine similarity function is working correctly.
This script tests both the original implementations and the new centralized function.
"""

import time
import logging
from scipy.spatial.distance import cosine
from backend.app.core.singletons import embed_texts, calculate_cosine_similarity, get_logger

logger = get_logger()
logger.setLevel(logging.INFO)

def original_cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors (original implementation)."""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = (sum(a * a for a in vec1)) ** 0.5
    magnitude2 = (sum(b * b for b in vec2)) ** 0.5
    
    if magnitude1 > 0 and magnitude2 > 0:
        return dot_product / (magnitude1 * magnitude2)
    else:
        return 0.0

def test_similarity_functions():
    """Test and compare different similarity calculation methods."""
    # Test texts
    texts = [
        "Climate change is a major global challenge",
        "Global warming is affecting the planet",
        "Artificial intelligence is transforming industries",
        "Machine learning algorithms can predict patterns"
    ]
    
    logger.info("Embedding test texts...")
    start_time = time.time()
    # Get embeddings for all texts at once
    embeddings = embed_texts(texts)
    embedding_time = time.time() - start_time
    logger.info(f"Embeddings generated in {embedding_time:.4f} seconds")
    
    # Compare different similarity calculation methods
    logger.info("\nComparing similarity calculation methods:")
    
    for i in range(len(texts)):
        for j in range(i+1, len(texts)):
            logger.info(f"\nTexts: '{texts[i]}' and '{texts[j]}'")
            
            # Method 1: Original implementation
            start_time = time.time()
            sim1 = original_cosine_similarity(embeddings[i], embeddings[j])
            time1 = time.time() - start_time
            
            # Method 2: Centralized implementation
            start_time = time.time()
            sim2 = calculate_cosine_similarity(embeddings[i], embeddings[j])
            time2 = time.time() - start_time
            
            # Method 3: SciPy implementation (for validation)
            start_time = time.time()
            sim3 = 1 - cosine(embeddings[i], embeddings[j])  # Convert distance to similarity
            time3 = time.time() - start_time
            
            logger.info(f"Original implementation: {sim1:.6f} in {time1:.6f}s")
            logger.info(f"Centralized implementation: {sim2:.6f} in {time2:.6f}s")
            logger.info(f"SciPy implementation: {sim3:.6f} in {time3:.6f}s")
            
            # Check if the results are close enough
            if abs(sim1 - sim2) > 1e-6 or abs(sim1 - sim3) > 1e-6:
                logger.warning("Discrepancy in similarity calculations!")
            else:
                logger.info("All similarity calculations match!")

def test_with_different_embedding_formats():
    """Test the centralized similarity function with different embedding formats."""
    # Single text and list of texts
    text1 = "Climate change is a major global challenge"
    text2 = "Global warming is affecting the planet"
    
    # Test with single strings
    emb1 = embed_texts(text1)
    emb2 = embed_texts(text2)
    
    # Test with list of strings
    emb_list = embed_texts([text1, text2])
    
    logger.info("\nTesting with different embedding formats:")
    
    # Test with single embeddings
    sim1 = calculate_cosine_similarity(emb1, emb2)
    logger.info(f"Similarity between single embeddings: {sim1:.6f}")
    
    # Test with first embedding from list and single embedding
    sim2 = calculate_cosine_similarity(emb_list[0], emb2)
    logger.info(f"Similarity between list[0] and single: {sim2:.6f}")
    
    # Test with single embedding and first embedding from list
    sim3 = calculate_cosine_similarity(emb1, emb_list[0])
    logger.info(f"Similarity between single and list[0]: {sim3:.6f}")
    
    # Verify results are consistent
    if abs(sim1 - sim2) > 1e-6 or abs(sim1 - sim3) > 1e-6:
        logger.warning("Inconsistency in similarity calculations with different formats!")
    else:
        logger.info("All similarity calculations with different formats match!")

if __name__ == "__main__":
    logger.info("Starting similarity function tests...")
    test_similarity_functions()
    test_with_different_embedding_formats()
    logger.info("Tests completed.")



