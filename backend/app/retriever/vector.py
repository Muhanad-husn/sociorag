"""Vector retrieval and cross-encoder reranking module for SocioGraph."""

# Import both options for loading rerankers
from sentence_transformers import CrossEncoder
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers.pipelines import pipeline
import torch
from backend.app.core.singletons import get_logger, get_chroma, embed_texts
from backend.app.retriever.vector_utils import batch_similarity, text_similarity
from backend.app.core.config import get_config

# Initialize logger and config
_logger = get_logger()
_cfg = get_config()

# Initialize cross-encoder reranker (lazy-loaded)
_reranker = None
_tokenizer = None
_model = None
_reranker_available = True
_direct_model_available = False  # Start with False until we confirm it works

def _get_reranker():
    """Lazy-load the cross-encoder reranker with caching support."""
    global _reranker, _reranker_available
    
    if _reranker is None and _reranker_available:
        try:
            from backend.app.core.config import get_config
            config = get_config()
            cache_dir = str(config.SENTENCE_TRANSFORMERS_CACHE_DIR)
            
            # Use same model that works with direct transformer but with specific parameters
            model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"  # Note the "-" in L-6 versus L6 in config
            _logger.info(f"Loading cross-encoder reranker: {model_name}")
            _logger.info(f"Using cache directory: {cache_dir}")
            
            _reranker = CrossEncoder(
                model_name, 
                max_length=512, 
                device="cpu",
                cache_folder=cache_dir
            )
            _logger.info("Successfully loaded cross-encoder reranker from cache")
        except Exception as e:
            _logger.warning(f"Failed to load cross-encoder reranker: {e}")
            _logger.warning("Will skip reranking and use vector similarity scores only")
            _reranker_available = False
            # Try with a public, non-authenticated model as fallback
            try:
                # Try the model from config but with the correct name format
                fallback_model = "cross-encoder/ms-marco-MiniLM-L-6-v2"  # Correct format with hyphen
                _logger.info(f"Attempting to load fallback reranker: {fallback_model}")
                
                from backend.app.core.config import get_config
                config = get_config()
                cache_dir = str(config.SENTENCE_TRANSFORMERS_CACHE_DIR)
                
                _reranker = CrossEncoder(
                    fallback_model, 
                    max_length=512, 
                    device="cpu",
                    cache_folder=cache_dir
                )
                _reranker_available = True
                _logger.info("Successfully loaded fallback reranker from cache")
            except Exception as e2:
                _logger.error(f"All reranker loading attempts failed: {e2}")
                _reranker_available = False
            
    return _reranker

def _load_direct_transformer():
    """Load reranker model directly using transformers library as a fallback with caching."""
    global _tokenizer, _model, _direct_model_available
    
    if _tokenizer is None or _model is None:
        try:
            from backend.app.core.config import get_config
            config = get_config()
            cache_dir = str(config.TRANSFORMERS_CACHE_DIR)
            
            fallback_model = "cross-encoder/ms-marco-MiniLM-L-6-v2"  # Public model that should work without auth
            _logger.info(f"Loading direct transformer reranker: {fallback_model}")
            _logger.info(f"Using cache directory: {cache_dir}")
            
            _tokenizer = AutoTokenizer.from_pretrained(fallback_model, cache_dir=cache_dir)
            _model = AutoModelForSequenceClassification.from_pretrained(fallback_model, cache_dir=cache_dir)
            _model.eval()  # Set to evaluation mode
            _direct_model_available = True
            _logger.info("Successfully loaded direct transformer reranker from cache")
            
        except Exception as e:
            _logger.error(f"Failed to load direct transformer reranker: {e}")
            _direct_model_available = False
    
    return _tokenizer, _model, _direct_model_available

def retrieve_chunks(query_emb=None, query_text=None, use_cache: bool = True, top_k: int = None):
    """Retrieve chunks from vector store based on query embedding or text.
    
    Args:
        query_emb: Query embedding vector (optional if query_text is provided)
        query_text: Query text to embed (optional if query_emb is provided)
        use_cache: Whether to use the embedding cache (default: True)
        top_k: Optional override for number of vector results to retrieve
        
    Returns:
        List of document chunks with similarity >= CHUNK_SIM
    """
    # Use provided top_k or fall back to config value
    k = top_k if top_k is not None else _cfg.TOP_K
    _logger.info(f"Retrieving chunks with similarity >= {_cfg.CHUNK_SIM}, top_k={k}")
    vectordb = get_chroma()
    
    # Use EmbeddingSingleton if text is provided but no embedding
    if query_emb is None and query_text is not None:
        _logger.info(f"Generating embedding for query text: {query_text}")
        try:
            query_emb = embed_texts(query_text, use_cache=use_cache)
            _logger.info(f"Successfully embedded query text")
        except Exception as e:
            _logger.error(f"Error embedding query text: {e}")
            return []
    
    # Ensure we have a valid embedding
    if query_emb is None:
        _logger.error("No query embedding or text provided")
        return []
      # Get raw documents - use provided top_k or fall back to config value
    k = top_k if top_k is not None else _cfg.TOP_K
    docs = vectordb.similarity_search_by_vector(
        query_emb, 
        k=k
    )
    
    _logger.info(f"Retrieved {len(docs)} initial chunks from vector store")
    return docs

def rerank_chunks(query: str, docs, top_k_rerank: int = None):
    """Rerank chunks using cross-encoder model.
    
    Args:
        query: Original query string (English)
        docs: List of document chunks from vector retrieval
        top_k_rerank: Optional override for number of results to keep after reranking
        
    Returns:
        List of reranked chunks (top TOP_K_RERANK)
    """
    if not docs:
        _logger.warning("No documents to rerank")
        return []
    
    _logger.info(f"Reranking {len(docs)} chunks using cross-encoder")
    
    # Get reranker (or check if available)
    reranker = _get_reranker()
      # If reranker is available, use it to rerank docs
    if reranker is not None and _reranker_available:
        try:
            # Create query-document pairs for reranking
            pairs = [(query, d.page_content) for d in docs]
            
            # Get reranker scores
            scores = reranker.predict(pairs)
              # Sort by score and take top k
            ranked = sorted(zip(docs, scores), key=lambda t: t[1], reverse=True)
            k_rerank = top_k_rerank if top_k_rerank is not None else _cfg.TOP_K_RERANK
            top_k = ranked[:k_rerank]
            
            _logger.info(f"Top reranked score: {top_k[0][1] if top_k else 'N/A'}")
            _logger.info(f"Returning top {len(top_k)} reranked chunks")
            
            return [d for d, _ in top_k]
        except Exception as e:
            _logger.error(f"Error during reranking: {e}")
            _logger.warning("Trying direct transformer fallback...")
              # Try direct transformer approach as a fallback
            direct_results = _rerank_with_direct_transformer(query, docs, top_k_rerank)
            if direct_results is not None:
                _logger.info("Successfully used direct transformer reranker")
                return direct_results
            
            _logger.warning("All reranking methods failed, falling back to vector similarity ordering")
    else:
        _logger.warning("CrossEncoder reranker not available, trying direct transformer...")
          # Try direct transformer approach
        direct_results = _rerank_with_direct_transformer(query, docs, top_k_rerank)
        if direct_results is not None:
            _logger.info("Successfully used direct transformer reranker")
            return direct_results
        
        # If direct transformer also fails, _rerank_with_direct_transformer will try embedding similarity
      # We shouldn't get here unless all fallbacks failed
    _logger.warning("All reranking methods failed, using original vector similarity ordering")
    k_rerank = top_k_rerank if top_k_rerank is not None else _cfg.TOP_K_RERANK
    return docs[:min(len(docs), k_rerank)]

def _rerank_with_direct_transformer(query, docs, top_k_rerank=None):
    """Rerank chunks using direct transformer model (without sentence_transformers).
    
    Args:
        query: Original query string
        docs: List of document chunks
        top_k_rerank: Number of results to keep after reranking
    """
    _logger.info("Attempting reranking with direct transformer model")
    
    tokenizer, model, is_available = _load_direct_transformer()
    
    if not is_available or tokenizer is None or model is None:
        _logger.warning("Direct transformer model not available, using embedding similarity as fallback")
        return _rerank_with_embeddings(query, docs)
    
    try:
        # Create pairs and compute scores
        pairs = [(query, d.page_content) for d in docs]
        scores = []
        
        for q, d in pairs:
            # Tokenize the pair
            inputs = tokenizer(q, d, return_tensors="pt", max_length=512, 
                               truncation=True, padding=True)
            
            # Get prediction
            with torch.no_grad():
                outputs = model(**inputs)
                # For cross-encoders, the score is usually a single value for binary tasks
                if outputs.logits.numel() == 1:
                    score = outputs.logits.item()
                else:
                    # If model outputs multiple logits, take the highest one or most relevant
                    score = outputs.logits[0, 0].item()  # Often the first logit is relevance score
                scores.append(score)
          # Sort by score and take top k
        ranked = sorted(zip(docs, scores), key=lambda t: t[1], reverse=True)
        k_rerank = top_k_rerank if top_k_rerank is not None else _cfg.TOP_K_RERANK
        top_k = ranked[:k_rerank]
        
        _logger.info(f"Direct transformer top score: {top_k[0][1] if top_k else 'N/A'}")
        return [d for d, _ in top_k]
        
    except Exception as e:
        _logger.error(f"Error during direct transformer reranking: {e}")
        _logger.warning("Falling back to embedding similarity reranking")
        return _rerank_with_embeddings(query, docs)

def _rerank_with_embeddings(query, docs, top_k_rerank=None):
    """Rerank chunks using embedding similarity as last resort fallback.
    
    This uses the EmbeddingSingleton to get consistent embeddings and compute
    cosine similarity between the query and each document.
    
    Args:
        query: Original query string
        docs: List of document chunks
        top_k_rerank: Number of results to keep after reranking
    """
    _logger.info("Attempting reranking with embedding similarity")
    
    try:
        if not docs:
            return []
            
        # Extract document texts
        doc_texts = [d.page_content for d in docs]
        
        # Use the text_similarity function from vector_utils
        scores = text_similarity(query, doc_texts)
          # Sort by similarity score and take top k
        ranked = sorted(zip(docs, scores), key=lambda t: t[1], reverse=True)
        k_rerank = top_k_rerank if top_k_rerank is not None else _cfg.TOP_K_RERANK
        top_k = ranked[:k_rerank]
        
        _logger.info(f"Embedding similarity top score: {top_k[0][1] if top_k else 'N/A'}")
        return [d for d, _ in top_k]
    except Exception as e:
        _logger.error(f"Error during embedding similarity reranking: {e}")
        k_rerank = top_k_rerank if top_k_rerank is not None else _cfg.TOP_K_RERANK
        return docs[:min(len(docs), k_rerank)]
