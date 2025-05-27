"""Graph retrieval module for SocioGraph."""

from typing import List, Dict
import sqlite3

from app.core.singletons import get_nlp, get_sqlite, get_logger
from app.core.config import get_config
from app.retriever.vector_utils import calculate_cosine_similarity
from app.retriever.sqlite_vec_utils import (
    get_entity_by_embedding, 
    get_entity_by_text, 
    binary_to_embedding
)

# Initialize singletons and config
_logger = get_logger()
_cfg = get_config()
_nlp = get_nlp()

# Use the centralized cosine_similarity from vector_utils
cosine_similarity = calculate_cosine_similarity

def _fetch_entity_hits(noun: str, use_cache: bool = True) -> List[Dict]:
    """Fetch entity hits from the graph database.
    
    Args:
        noun: The noun to search for
        use_cache: Whether to use the embedding cache (default: True)
        
    Returns:
        List of entity records with similarity >= GRAPH_SIM
    """    
    try:
        _logger.debug(f"Searching for entity '{noun}' with similarity >= {_cfg.GRAPH_SIM}")
        
        # Try vector-based search first with parallel processing
        hits = get_entity_by_embedding(
            noun, 
            similarity_threshold=_cfg.GRAPH_SIM,
            use_parallel=True,
            use_cache=use_cache
        )
        
        if hits:
            _logger.info(f"Found {len(hits)} entities using vector search for '{noun}'")
            return hits
            
        # Fallback to text-based search
        _logger.info(f"No vector matches found, using text-based search for '{noun}'")
        text_hits = get_entity_by_text(noun, limit=10)
        
        # Add default similarity score for text-based matches
        for hit in text_hits:
            hit['similarity'] = _cfg.GRAPH_SIM
            
        _logger.info(f"Found {len(text_hits)} entities using text search for '{noun}'")
        return text_hits
        
    except Exception as e:
        _logger.error(f"Error fetching entity hits: {e}")
        return []

def retrieve_triples(query_en: str) -> List[Dict]:
    """Retrieve graph triples related to the query.
    
    Args:
        query_en: English query text
        
    Returns:
        List of relation triples
    """
    _logger.info("Extracting nouns from query")
    doc = _nlp(query_en)
    nouns = [t.text.lower() for t in doc if t.pos_ == "NOUN"]
    
    _logger.info(f"Extracted nouns: {nouns}")
    
    con = get_sqlite()
    triples = []
    
    for noun in nouns:
        entity_hits = _fetch_entity_hits(noun)
        
        for hit in entity_hits:
            # Get all relations where this entity is either head or tail
            try:
                rows = con.execute("""
                    SELECT r.id, r.source_id, s.name as source_name, r.target_id, 
                           t.name as target_name, r.relation_type
                    FROM relation r
                    JOIN entity s ON r.source_id = s.id
                    JOIN entity t ON r.target_id = t.id
                    WHERE r.source_id = ? OR r.target_id = ?
                """, (hit["id"], hit["id"])).fetchall()
                
                for row in rows:
                    # Check if row is a dict-like object or a tuple
                    if hasattr(row, 'keys'):
                        # Dict-like object (sqlite3.Row)
                        triple = {
                            "id": row["id"],
                            "source_id": row["source_id"],
                            "source_name": row["source_name"],
                            "target_id": row["target_id"],
                            "target_name": row["target_name"],
                            "relation_type": row["relation_type"],
                            "matched_entity": hit["name"],
                            "matched_similarity": hit["similarity"]
                        }
                    else:
                        # Tuple
                        triple = {
                            "id": row[0],
                            "source_id": row[1],
                            "source_name": row[2],
                            "target_id": row[3],
                            "target_name": row[4],
                            "relation_type": row[5],
                            "matched_entity": hit["name"],
                            "matched_similarity": hit["similarity"]
                        }
                    triples.append(triple)
                    
                _logger.debug(f"Found {len(rows)} relations for entity '{hit['name']}'")
            except Exception as e:
                _logger.error(f"Error retrieving triples: {e}")
    
    _logger.info(f"Retrieved {len(triples)} total triples")
    return triples
