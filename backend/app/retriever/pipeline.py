"""Main retrieval pipeline orchestrator for SocioGraph."""

from typing import Dict, Any

from backend.app.core.singletons import get_logger, embed_texts
from backend.app.retriever.language import normalize_query
from backend.app.retriever.vector import retrieve_chunks, rerank_chunks
# Use the improved graph module
try:
    from backend.app.retriever.graph_improved import retrieve_triples
    _logger = get_logger()
    _logger.info("Using improved graph retrieval module")
except ImportError:
    from backend.app.retriever.graph import retrieve_triples
    _logger = get_logger()
    _logger.warning("Falling back to original graph retrieval module")
    
from backend.app.retriever.merge import merge_context

# Initialize logger
_logger = get_logger()

def retrieve_context(user_query: str) -> Dict[str, Any]:
    """Main entry point for the retrieval pipeline.
    
    Orchestrates the full retrieval process:
    1. Language detection and translation
    2. Vector retrieval of chunks
    3. Cross-encoder reranking
    4. Graph retrieval of relevant triples
    5. Context merging with token budgeting
    
    Args:
        user_query: Raw user query in English or Arabic
        
    Returns:
        Dictionary with retrieval results:
        {
            "lang": language code ("en" or "ar"),
            "query_en": English version of the query,
            "chunks": List of retrieved and reranked chunks,
            "triples": List of retrieved graph triples,
            "context": Merged context result dictionary
        }
    """
    start_time = __import__('time').time()
    _logger.info(f"Starting retrieval for query: {user_query}")
      # Step 1: Language detection and translation
    lang, query_en = normalize_query(user_query)
    _logger.info(f"Normalized query: lang={lang}, text={query_en}")
    
    # Step 2: Vector embedding and retrieval
    # Pass the query text directly to retrieve_chunks which will handle embedding
    _logger.info("Retrieving chunks using query text")
    raw_chunks = retrieve_chunks(query_text=query_en)
    
    # Step 3: Cross-encoder reranking
    _logger.info("Reranking chunks")
    chunks = rerank_chunks(query_en, raw_chunks)
    
    # Step 4: Graph retrieval
    _logger.info("Retrieving graph triples")
    triples = retrieve_triples(query_en)
    
    # Step 5: Context merging
    _logger.info("Merging context")
    context = merge_context(chunks, triples)
    
    # Build final result
    result = {
        "lang": lang,
        "query_en": query_en,
        "chunks": chunks,
        "triples": triples,
        "context": context
    }
    
    elapsed = __import__('time').time() - start_time
    _logger.info(f"Retrieval completed in {elapsed:.2f}s")
    
    return result
