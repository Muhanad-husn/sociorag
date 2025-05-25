#!/usr/bin/env python
"""
Test script for the improved entity extraction module.

This script tests the entity extraction module with sample chunks.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.core.singletons import get_logger
from backend.app.ingest.entity_extraction import extract_entities_from_text


logger = get_logger()

# Sample chunks with clear entities and relationships
SAMPLE_CHUNKS = [
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
    """
]


async def test_entity_extraction():
    """Test the entity extraction module with sample chunks."""
    logger.info("Testing entity extraction module...")
    
    for i, chunk in enumerate(SAMPLE_CHUNKS):
        print(f"\n{'='*60}\nTesting chunk {i+1}\n{'='*60}\n")
        print(f"Text chunk:\n{chunk}")
        
        # Extract entities using the module
        entities = await extract_entities_from_text(chunk)
        
        if entities:
            print(f"\nSuccessfully extracted {len(entities)} entities:")
            for j, entity in enumerate(entities):
                print(f"  {j+1}. {entity['head']} ({entity['head_type']}) {entity['relation']} {entity['tail']} ({entity['tail_type']})")
        else:
            print("\nNo entities extracted.")


if __name__ == "__main__":
    print("Testing improved entity extraction module...")
    asyncio.run(test_entity_extraction())
