#!/usr/bin/env python
"""
Test script for the enhanced entity extraction module with advanced features.

This script tests the enhanced entity extraction module with:
- Retry mechanism
- Caching
- Batch processing
- Structured error reporting
"""

import asyncio
import json
import sys
import time
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.core.singletons import get_logger
from backend.app.ingest.enhanced_entity_extraction import (
    extract_entities_from_text, 
    extract_entities_with_retry,
    batch_process_chunks,
    clear_cache
)


logger = get_logger()

# Sample chunks for testing (enhanced set)
ENHANCED_SAMPLE_CHUNKS = [
    """
    The United Nations (UN) has identified climate change as the defining issue of our time. 
    The Intergovernmental Panel on Climate Change (IPCC) was established by the UN to provide 
    scientific assessments on climate change. According to the Paris Agreement, signed in 2015, 
    countries committed to limit global warming to well below 2 degrees Celsius. 
    The European Union has been a strong supporter of the Paris Agreement.
    """,
    
    """
    The World Health Organization (WHO) coordinates international health efforts. 
    Dr. Tedros Adhanom Ghebreyesus currently serves as the Director-General of WHO. 
    WHO played a crucial role during the COVID-19 pandemic, providing guidance to countries.
    The United States and China are among the major contributors to the WHO budget.
    """,
    
    """
    Microsoft was founded by Bill Gates and Paul Allen on April 4, 1975.
    Satya Nadella is the current CEO of Microsoft, having succeeded Steve Ballmer in 2014.
    Microsoft acquired GitHub in 2018 for $7.5 billion.
    Microsoft Azure is a cloud computing service competing with Amazon Web Services (AWS).
    """,
    
    """
    The Great Wall of China is one of the most famous landmarks in the world.
    It was built to protect Chinese states from invasions.
    The wall stretches over 13,000 miles and took centuries to complete.
    It is a UNESCO World Heritage site and attracts millions of visitors annually.
    """,
    
    """
    The theory of relativity was developed by Albert Einstein.
    It revolutionized the understanding of space, time, and gravity.
    The theory is divided into two parts: special relativity and general relativity.
    It has been confirmed by many experiments and is a cornerstone of modern physics.
    """,
    
    """
    The Amazon Rainforest is the largest tropical rainforest in the world.
    It is home to an incredible diversity of species, many of which are not found anywhere else.
    The rainforest plays a crucial role in regulating the Earth's climate.
    Deforestation and climate change pose significant threats to this vital ecosystem.
    """
]


async def test_simple_extraction():
    """Test basic entity extraction."""
    print("\n=== Testing Basic Entity Extraction ===\n")
    chunk = ENHANCED_SAMPLE_CHUNKS[0]
    
    print(f"Text chunk:\n{chunk}")
    
    # Extract entities
    entities = await extract_entities_from_text(chunk)
    
    if entities:
        print(f"\nSuccessfully extracted {len(entities)} entities:")
        for i, entity in enumerate(entities):
            print(f"  {i+1}. {entity['head']} ({entity['head_type']}) {entity['relation']} {entity['tail']} ({entity['tail_type']})")
    else:
        print("\nNo entities extracted.")


async def test_extraction_with_retry():
    """Test entity extraction with retry and debug info."""
    print("\n=== Testing Entity Extraction with Retry ===\n")
    chunk = ENHANCED_SAMPLE_CHUNKS[1]
    
    print(f"Text chunk:\n{chunk}")
    
    # Extract entities with retry
    start_time = time.time()
    entities, debug_info = await extract_entities_with_retry(chunk)
    elapsed = time.time() - start_time
    
    # Print debug info
    print(f"\nExtraction completed in {elapsed:.2f} seconds")
    print(f"Attempts: {debug_info['attempts']}")
    print(f"Success: {debug_info['success']}")
    print(f"From cache: {debug_info['from_cache']}")
    
    if debug_info['parsing_info']:
        print(f"Parsing strategy: {debug_info['parsing_info']['strategy_used']}")
        print(f"Parsing attempts: {debug_info['parsing_info']['parsing_attempts']}")
        print(f"Valid entities: {debug_info['parsing_info']['valid_entity_count']}")
    
    if debug_info['error']:
        print(f"Error: {debug_info['error']}")
    
    # Print entities
    if entities:
        print(f"\nSuccessfully extracted {len(entities)} entities:")
        for i, entity in enumerate(entities):
            print(f"  {i+1}. {entity['head']} ({entity['head_type']}) {entity['relation']} {entity['tail']} ({entity['tail_type']})")
    else:
        print("\nNo entities extracted.")
    
    # Test cache by running again
    print("\n=== Testing Cache Functionality ===\n")
    start_time = time.time()
    cached_entities, cached_debug_info = await extract_entities_with_retry(chunk)
    elapsed = time.time() - start_time
    
    print(f"Second extraction completed in {elapsed:.2f} seconds")
    print(f"From cache: {cached_debug_info['from_cache']}")
    print(f"Entities: {len(cached_entities)}")


async def test_batch_processing():
    """Test batch processing of multiple chunks."""
    print("\n=== Testing Batch Processing ===\n")
    
    # Clear cache before testing
    clear_cache()
    
    print(f"Processing {len(ENHANCED_SAMPLE_CHUNKS)} chunks in batch mode")
    
    # Process all chunks in batch
    start_time = time.time()
    batch_results = await batch_process_chunks(ENHANCED_SAMPLE_CHUNKS, batch_size=2, concurrency_limit=2)
    elapsed = time.time() - start_time
    
    # Print results
    print(f"\nBatch processing completed in {elapsed:.2f} seconds")
    
    total_entities = sum(len(entities) for entities in batch_results)
    print(f"Extracted {total_entities} entities from {len(ENHANCED_SAMPLE_CHUNKS)} chunks")
    
    for i, entities in enumerate(batch_results):
        print(f"\nChunk {i+1} ({len(entities)} entities):")
        for j, entity in enumerate(entities):
            print(f"  {j+1}. {entity['head']} ({entity['head_type']}) {entity['relation']} {entity['tail']} ({entity['tail_type']})")


async def main():
    """Run all tests."""
    await test_simple_extraction()
    await test_extraction_with_retry()
    await test_batch_processing()


if __name__ == "__main__":
    asyncio.run(main())
