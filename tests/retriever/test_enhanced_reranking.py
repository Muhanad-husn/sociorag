"""Test script to demonstrate the enhanced reranking with embedding fallback."""

import sys
import traceback
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

try:
    from backend.app.core.singletons import get_logger
    from backend.app.retriever.pipeline import retrieve_context
    
    # Get logger
    logger = get_logger()
    logger.info("Testing enhanced reranking with embedding fallback...")
    
    # Test query
    query = "What is a knowledge graph?"
    logger.info(f"Testing query: {query}")
    
    # Run retrieval
    results = retrieve_context(query)
      # Show results
    logger.info(f"Retrieved {len(results['chunks'])} chunks and {len(results['triples'])} triples")
    logger.info(f"Context tokens: {results['context']['total_tokens']}")
    
    # Print some sample chunks
    logger.info("Sample chunks (first 3):")
    for i, chunk in enumerate(results['chunks'][:3]):
        logger.info(f"Chunk {i+1}: {chunk.page_content[:100]}...")
    
    logger.info("Enhanced reranking test completed!")
    
except Exception as e:
    print(f"Error testing enhanced reranking: {e}")
    traceback.print_exc()



