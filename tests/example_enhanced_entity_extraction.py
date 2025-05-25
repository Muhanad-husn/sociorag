#!/usr/bin/env python
"""
Simple usage example for the enhanced entity extraction module.

This script demonstrates how to use the enhanced entity extraction module
with a focus on practical use cases.
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.ingest.enhanced_entity_extraction import (
    extract_entities_from_text,
    extract_entities_with_retry,
    batch_process_chunks,
    clear_cache
)


# Sample text to process
SAMPLE_TEXT = """
The United Nations (UN) was founded in 1945 after World War II to replace the League of Nations.
The UN's mission is to maintain international peace and security, develop friendly relations among nations,
achieve international cooperation, and be a center for harmonizing the actions of nations.
The Security Council is one of the six principal organs of the UN, charged with ensuring international peace and security.
The United States, Russia, China, France, and the United Kingdom are permanent members of the Security Council.
The General Assembly is the main deliberative organ of the UN where all member states have equal representation.
António Guterres is the current Secretary-General of the United Nations, having taken office on January 1, 2017.
"""

# Multiple chunks for batch processing
SAMPLE_CHUNKS = [
    """Microsoft was founded by Bill Gates and Paul Allen in 1975. 
    The company is headquartered in Redmond, Washington and is known for 
    products like Windows, Office, and Azure.""",
    
    """Apple Inc. was founded by Steve Jobs, Steve Wozniak, and Ronald Wayne in 1976.
    The company is headquartered in Cupertino, California and is known for 
    products like the iPhone, iPad, and Mac.""",
    
    """Google was founded by Larry Page and Sergey Brin in 1998.
    The company is headquartered in Mountain View, California and is known for
    products like Search, Maps, and Android."""
]


async def example_basic_extraction():
    """Demonstrate basic entity extraction."""
    print("\n=== Basic Entity Extraction ===\n")
    print("Sample text:")
    print(SAMPLE_TEXT[:150] + "...\n")
    
    # Extract entities from text
    entities = await extract_entities_from_text(SAMPLE_TEXT)
    
    # Display the extracted entities
    print(f"Extracted {len(entities)} entities:")
    for i, entity in enumerate(entities):
        print(f"  {i+1}. {entity['head']} ({entity['head_type']}) {entity['relation']} {entity['tail']} ({entity['tail_type']})")


async def example_extraction_with_retry():
    """Demonstrate entity extraction with retry and debug info."""
    print("\n=== Entity Extraction with Retry ===\n")
    
    # Extract entities with retry and debug info
    entities, debug_info = await extract_entities_with_retry(SAMPLE_TEXT, max_retries=2)
    
    # Display debug information
    print("Debug information:")
    print(f"  Attempts: {debug_info['attempts']}")
    print(f"  Success: {debug_info['success']}")
    print(f"  From cache: {debug_info['from_cache']}")
    
    if debug_info['parsing_info']:
        print(f"  Parsing strategy: {debug_info['parsing_info']['strategy_used']}")
        print(f"  Parsing attempts: {debug_info['parsing_info']['parsing_attempts']}")
    
    if debug_info['error']:
        print(f"  Error: {debug_info['error']}")
    
    # Display the extracted entities
    print(f"\nExtracted {len(entities)} entities")


async def example_batch_processing():
    """Demonstrate batch processing of multiple chunks."""
    print("\n=== Batch Processing ===\n")
    
    # Clear cache before testing
    clear_cache()
    
    print(f"Processing {len(SAMPLE_CHUNKS)} chunks in batch mode")
    
    # Process all chunks in batch
    batch_results = await batch_process_chunks(SAMPLE_CHUNKS, batch_size=2, concurrency_limit=2)
    
    # Display results
    print("\nBatch processing results:")
    
    total_entities = sum(len(entities) for entities in batch_results)
    print(f"Extracted {total_entities} entities from {len(SAMPLE_CHUNKS)} chunks")
    
    for i, entities in enumerate(batch_results):
        print(f"\nChunk {i+1} ({len(entities)} entities):")
        for j, entity in enumerate(entities):
            print(f"  {j+1}. {entity['head']} ({entity['head_type']}) {entity['relation']} {entity['tail']} ({entity['tail_type']})")


async def example_caching():
    """Demonstrate caching functionality."""
    print("\n=== Caching ===\n")
    
    # Clear cache
    clear_cache()
    print("Cache cleared")
    
    # First extraction (no cache)
    print("\nFirst extraction (no cache)...")
    _, debug_info1 = await extract_entities_with_retry(SAMPLE_TEXT)
    print(f"From cache: {debug_info1['from_cache']}")
    
    # Second extraction (should use cache)
    print("\nSecond extraction (should use cache)...")
    _, debug_info2 = await extract_entities_with_retry(SAMPLE_TEXT)
    print(f"From cache: {debug_info2['from_cache']}")


async def example_error_handling():
    """Demonstrate error handling with a problematic chunk."""
    print("\n=== Error Handling ===\n")
    
    # Create a problematic chunk (very short, might confuse the model)
    problematic_chunk = "A B C D E."
    
    print("Attempting extraction from problematic chunk...")
    
    # Try extraction with retry
    entities, debug_info = await extract_entities_with_retry(problematic_chunk, max_retries=2)
    
    print(f"Extraction success: {debug_info['success']}")
    print(f"Attempts: {debug_info['attempts']}")
    
    if debug_info['parsing_info'] and debug_info['parsing_info']['errors']:
        print("\nParsing errors:")
        for i, error in enumerate(debug_info['parsing_info']['errors'][:3]):  # Show first 3 errors
            print(f"  {i+1}. {error}")
    
    if debug_info['error']:
        print(f"\nExtraction error: {debug_info['error']}")
    
    print(f"\nExtracted {len(entities)} entities")


async def main():
    """Run all examples."""
    print("=== Enhanced Entity Extraction Examples ===")
    
    # Run examples
    await example_basic_extraction()
    await example_extraction_with_retry()
    await example_batch_processing()
    await example_caching()
    await example_error_handling()
    
    print("\n=== Examples Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
