#!/usr/bin/env python
"""
Manual entity injection script for SocioGraph.

This script bypasses the LLM entity extraction and directly inserts
sample entities and relationships into the database.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.core.singletons import get_sqlite, get_logger, embed_texts
from backend.app.ingest.pipeline import get_or_insert_entity, insert_graph_rows

logger = get_logger()

# Sample entities and relationships
SAMPLE_ENTITIES = [
    {
        "head": "United Nations",
        "head_type": "Organization",
        "relation": "IDENTIFIED",
        "tail": "climate change",
        "tail_type": "Issue"
    },
    {
        "head": "Intergovernmental Panel on Climate Change",
        "head_type": "Organization",
        "relation": "ESTABLISHED_BY",
        "tail": "United Nations",
        "tail_type": "Organization"
    },
    {
        "head": "Paris Agreement",
        "head_type": "Agreement",
        "relation": "SIGNED_IN",
        "tail": "2015",
        "tail_type": "Year"
    },
    {
        "head": "European Union",
        "head_type": "Organization",
        "relation": "SUPPORTS",
        "tail": "Paris Agreement",
        "tail_type": "Agreement"
    },
    {
        "head": "World Health Organization",
        "head_type": "Organization",
        "relation": "WARNED_ABOUT",
        "tail": "climate change",
        "tail_type": "Issue"
    },
    {
        "head": "Elon Musk",
        "head_type": "Person",
        "relation": "CEO_OF",
        "tail": "Tesla",
        "tail_type": "Company"
    },
    {
        "head": "Tesla",
        "head_type": "Company",
        "relation": "DEVELOPS",
        "tail": "electric vehicles",
        "tail_type": "Product"
    },
    {
        "head": "Microsoft",
        "head_type": "Company",
        "relation": "LED_BY",
        "tail": "Satya Nadella",
        "tail_type": "Person"
    },
    {
        "head": "Amazon Rainforest",
        "head_type": "Location",
        "relation": "LOCATED_IN",
        "tail": "Brazil",
        "tail_type": "Country"
    },
    {
        "head": "Green Climate Fund",
        "head_type": "Organization",
        "relation": "HELPS",
        "tail": "developing countries",
        "tail_type": "Entity"
    }
]

def insert_sample_entities():
    """Insert sample entities and relationships into the database."""
    logger.info("Inserting sample entities and relationships...")
    
    # Insert entities and relationships
    insert_graph_rows(SAMPLE_ENTITIES, "manual_sample")
    
    # Check if entities were inserted
    sqlite = get_sqlite()
    cursor = sqlite.execute("SELECT COUNT(*) FROM entity")
    num_entities = cursor.fetchone()[0]
    logger.info(f"Entities in graph database: {num_entities}")
    
    cursor = sqlite.execute("SELECT COUNT(*) FROM relation")
    num_relations = cursor.fetchone()[0]
    logger.info(f"Relations in graph database: {num_relations}")
    
    # Validation passed if we have entities and relations
    success = num_entities > 0 and num_relations > 0
    if success:
        logger.info("✅ Entity insertion PASSED!")
    else:
        logger.error("❌ Entity insertion FAILED: No entities or relations detected.")
    
    return success

if __name__ == "__main__":
    success = insert_sample_entities()
    # Exit with appropriate status code
    sys.exit(0 if success else 1)
