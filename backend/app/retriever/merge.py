"""Context merging and token budgeting for SocioGraph."""

import tiktoken
from typing import List, Dict, Any

from app.core.singletons import get_logger
from app.core.config import get_config

# Initialize logger and config
_logger = get_logger()
_cfg = get_config()

# Initialize tiktoken encoder (lazy-loaded)
_encoder = None

def _get_encoder():
    """Lazy-load the tiktoken encoder."""
    global _encoder
    if _encoder is None:
        # Use GPT-4 encoding as safe default
        _encoder = tiktoken.encoding_for_model("gpt-4o")
    return _encoder

def format_triple(triple: Dict) -> str:
    """Format a triple as a human-readable string.
    
    Args:
        triple: The triple dictionary from the database
        
    Returns:
        Formatted string representation
    """
    return f"{triple['source_name']} {triple['relation_type']} {triple['target_name']}"

def merge_context(chunks: List, triples: List[Dict], context_window: int = 8192) -> Dict:
    """Merge chunks and triples into a single context block.
    
    Args:
        chunks: List of document chunks
        triples: List of relation triples
        context_window: The model's context window size
        
    Returns:
        Dictionary with merged context and token stats
    """
    encoder = _get_encoder()
    
    # Calculate token budget (default 40% of context window)
    max_tokens = int(context_window * _cfg.MAX_CONTEXT_FRACTION)
    _logger.info(f"Token budget: {max_tokens} tokens (from {context_window} window)")
    
    # Extract texts from chunks
    chunk_texts = [d.page_content for d in chunks]
    
    # Format triples as strings
    triple_texts = [format_triple(t) for t in triples]
    
    # Prioritize chunks over triples
    combined = chunk_texts + triple_texts
    
    # Track token usage
    final_texts = []
    total_tokens = 0
    chunk_tokens = 0
    triple_tokens = 0
    
    # Fit texts into token budget
    for i, text in enumerate(combined):
        # Encode to count tokens
        tokens = encoder.encode(text)
        token_count = len(tokens)
        
        # Check if adding this text would exceed budget
        if total_tokens + token_count > max_tokens:
            _logger.info(f"Token budget reached at item {i}/{len(combined)}")
            break
            
        # Add text and update token counts
        final_texts.append(text)
        total_tokens += token_count
        
        # Track tokens by source type
        if i < len(chunk_texts):
            chunk_tokens += token_count
        else:
            triple_tokens += token_count
    
    # Build result with statistics
    result = {
        "merged_texts": final_texts,
        "total_tokens": total_tokens,
        "chunk_tokens": chunk_tokens,
        "triple_tokens": triple_tokens,
        "chunks_included": min(len(final_texts), len(chunk_texts)),
        "triples_included": max(0, min(len(final_texts) - len(chunk_texts), len(triple_texts))),
        "max_tokens": max_tokens
    }
    
    _logger.info(f"Final context: {result['total_tokens']} tokens, " 
                 f"{result['chunks_included']}/{len(chunk_texts)} chunks, "
                 f"{result['triples_included']}/{len(triple_texts)} triples")
                 
    return result
