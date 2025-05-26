"""Test script to demonstrate embedding singleton functionality."""

import sys
import traceback
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

try:
    from backend.app.core.singletons import embed_texts, get_logger

    # Get logger
    logger = get_logger()
    logger.info("Testing embedding singleton...")

    # Test single text embedding
    text = "This is a test of the embedding singleton"
    logger.info(f"Embedding text: '{text}'")
    embedding = embed_texts(text)
    logger.info(f"Got embedding with {len(embedding)} dimensions")
    logger.info(f"First 5 values: {embedding[:5]}")

    # Test multiple texts embedding
    texts = ["Hello world", "Testing embeddings", "Knowledge graph"]
    logger.info(f"Embedding multiple texts: {texts}")
    embeddings = embed_texts(texts)
    logger.info(f"Got {len(embeddings)} embeddings, each with {len(embeddings[0])} dimensions")

    # Show similarity between texts by cosine distance
    import numpy as np
    from scipy.spatial.distance import cosine

    logger.info("Computing similarities between texts:")
    for i in range(len(texts)):
        for j in range(i+1, len(texts)):
            similarity = 1 - cosine(embeddings[i], embeddings[j])
            logger.info(f"Similarity between '{texts[i]}' and '{texts[j]}': {similarity:.4f}")

    logger.info("Embedding singleton test completed successfully!")
    
    # Print directly to stdout as well in case logger isn't showing output
    print("\nEmbedding test results:")
    print(f"- Single text embedding dimensions: {len(embedding)}")
    print(f"- Multiple text embeddings: {len(embeddings)} with dimensions {len(embeddings[0])}")
    print("- Test completed successfully!")
except Exception as e:
    print(f"Error testing embedding singleton: {e}")
    traceback.print_exc()



