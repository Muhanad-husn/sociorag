"""
Enhanced vector utilities module for SocioGraph.

This module provides improved vector similarity functions that use the
EmbeddingSingleton for consistent embeddings and similarity calculations.
"""

from typing import List, Union, Any, TypeVar, cast, Optional
import concurrent.futures
from functools import partial

from app.core.singletons import embed_texts, get_logger

# Initialize logger
_logger = get_logger()

def extract_vector(embedding: Union[List[float], List[List[float]]]) -> List[float]:
    """Extract a flat vector from potentially nested embeddings.
    
    Args:
        embedding: An embedding vector or list of embedding vectors
        
    Returns:
        A flat list of floats representing the embedding vector
    """
    # Handle case where embedding is a list of lists (batch embeddings)
    if isinstance(embedding, list) and embedding and isinstance(embedding[0], list):
        return embedding[0]  # Take first embedding from batch
    return embedding  # Already a flat list

def calculate_cosine_similarity(vec1: Union[List[float], List[List[float]]], 
                              vec2: Union[List[float], List[List[float]]]) -> float:
    """Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector as a list of float values or list of list of float values
        vec2: Second vector as a list of float values or list of list of float values
        
    Returns:
        Cosine similarity score between 0 and 1
    """
    # Extract flat vectors
    v1 = extract_vector(vec1)
    v2 = extract_vector(vec2)
    
    try:
        # Calculate dot product
        dot_product = sum(v1[i] * v2[i] for i in range(min(len(v1), len(v2))))
        
        # Calculate magnitudes
        magnitude1 = sum(v * v for v in v1) ** 0.5
        magnitude2 = sum(v * v for v in v2) ** 0.5
        
        # Calculate cosine similarity
        if magnitude1 > 0 and magnitude2 > 0:
            return float(dot_product / (magnitude1 * magnitude2))
    except (TypeError, IndexError) as e:
        _logger.warning(f"Error in cosine similarity calculation: {e}")
    
    return 0.0

def _process_similarity_batch(
    query_embedding: Union[List[float], List[List[float]]],
    doc_batch: List[Union[List[float], List[List[float]]]]
) -> List[float]:
    """Process a batch of document embeddings for similarity calculation.
    
    Args:
        query_embedding: Query embedding vector
        doc_batch: Batch of document embedding vectors
        
    Returns:
        List of similarity scores for the batch
    """
    return [calculate_cosine_similarity(query_embedding, doc_emb) for doc_emb in doc_batch]

def batch_similarity(
    query_embedding: Union[List[float], List[List[float]]], 
    doc_embeddings: List[Union[List[float], List[List[float]]]],
    use_parallel: bool = True,
    max_workers: int = 4
) -> List[float]:
    """Calculate batch similarity between a query and multiple documents.
    
    Args:
        query_embedding: Query embedding vector
        doc_embeddings: List of document embedding vectors
        use_parallel: Whether to use parallel processing (default: True)
        max_workers: Maximum number of worker threads for parallel processing (default: 4)
        
    Returns:
        List of similarity scores
    """
    # For small batches, process sequentially
    if len(doc_embeddings) < 10 or not use_parallel:
        return _process_similarity_batch(query_embedding, doc_embeddings)
    
    # For larger batches, use parallel processing
    batch_size = max(10, len(doc_embeddings) // max_workers)
    batches = [doc_embeddings[i:i + batch_size] for i in range(0, len(doc_embeddings), batch_size)]
    
    _logger.debug(f"Processing similarity in {len(batches)} batches with up to {max_workers} workers")
      # Create partial function with fixed query embedding
    def process_batch_with_query(doc_batch):
        return _process_similarity_batch(query_embedding, doc_batch)
    
    # Process batches in parallel
    scores = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        batch_results = executor.map(process_batch_with_query, batches)
        for batch_result in batch_results:
            scores.extend(batch_result)
    
    return scores

def text_similarity(query: str, docs: List[str]) -> List[float]:
    """Calculate similarity between a query text and document texts.
    
    Args:
        query: Query text
        docs: List of document texts
        
    Returns:
        List of similarity scores
    """
    # Embed query and documents
    query_embedding = embed_texts(query)
    
    # For efficiency, embed all documents at once if there aren't too many
    if len(docs) <= 100:  # Batch size limit
        doc_embeddings = embed_texts(docs)
    else:
        # Process in batches if there are many documents
        doc_embeddings = []
        batch_size = 50
        for i in range(0, len(docs), batch_size):
            batch = docs[i:i+batch_size]
            batch_embeddings = embed_texts(batch)
            doc_embeddings.extend(batch_embeddings)
    
    # Calculate similarities
    return batch_similarity(query_embedding, doc_embeddings)

def parallel_batch_similarity(
    query_embedding: Union[List[float], List[List[float]]], 
    doc_embeddings: List[Union[List[float], List[List[float]]]],
    max_workers: int = 4
) -> List[float]:
    """Calculate batch similarity between a query and multiple documents using parallel processing.
    
    Args:
        query_embedding: Query embedding vector
        doc_embeddings: List of document embedding vectors
        max_workers: Maximum number of worker threads (default: 4)
        
    Returns:
        List of similarity scores
    """
    if len(doc_embeddings) <= 10:
        # For small batches, use sequential processing to avoid overhead
        return batch_similarity(query_embedding, doc_embeddings)
    
    # Split documents into batches for parallel processing
    batch_size = max(5, len(doc_embeddings) // max_workers)
    batches = [doc_embeddings[i:i + batch_size] for i in range(0, len(doc_embeddings), batch_size)]
    
    _logger.debug(f"Processing {len(doc_embeddings)} documents in {len(batches)} batches")
    
    # Process batches in parallel
    all_scores = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all batch jobs
        future_to_batch = {
            executor.submit(batch_similarity, query_embedding, batch): batch 
            for batch in batches
        }
        
        # Collect results in order
        for future in concurrent.futures.as_completed(future_to_batch):
            try:
                scores = future.result()
                all_scores.extend(scores)
            except Exception as e:
                _logger.warning(f"Error in parallel batch similarity: {e}")
                # Add zeros for failed batch
                batch = future_to_batch[future]
                all_scores.extend([0.0] * len(batch))
    
    return all_scores

def parallel_text_similarity(
    query: str, 
    docs: List[str], 
    max_workers: int = 4,
    use_cache: bool = True
) -> List[float]:
    """Calculate similarity between a query text and document texts using parallel processing.
    
    Args:
        query: Query text
        docs: List of document texts
        max_workers: Maximum number of worker threads (default: 4)
        use_cache: Whether to use the embedding cache (default: True)
        
    Returns:
        List of similarity scores
    """
    if len(docs) <= 50:
        # For small document sets, use the regular function
        return text_similarity(query, docs)
    
    # Embed query once
    query_embedding = embed_texts(query, use_cache=use_cache)
    
    # Process documents in parallel batches
    batch_size = max(25, len(docs) // max_workers)
    batches = [docs[i:i + batch_size] for i in range(0, len(docs), batch_size)]
    
    _logger.debug(f"Processing {len(docs)} documents in {len(batches)} batches for similarity")
    
    def process_doc_batch(doc_batch):
        """Process a batch of documents."""
        try:
            # Embed the batch of documents
            doc_embeddings = embed_texts(doc_batch, use_cache=use_cache)
            # Calculate similarities
            return batch_similarity(query_embedding, doc_embeddings)
        except Exception as e:
            _logger.warning(f"Error processing document batch: {e}")
            return [0.0] * len(doc_batch)
    
    # Process batches in parallel
    all_scores = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        batch_results = executor.map(process_doc_batch, batches)
        for batch_scores in batch_results:
            all_scores.extend(batch_scores)
    
    return all_scores

# No additional imports needed here
