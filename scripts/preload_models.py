#!/usr/bin/env python3
"""Preload all models to cache for faster startup.

This script downloads and caches all the models used by SocioRAG:
- Embedding models (SentenceTransformers)
- spaCy models
- Translation models (Helsinki-NLP)
- Reranking models (Cross-encoder)

Run this script once to significantly reduce startup time for subsequent runs.
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

def preload_all_models():
    """Download and cache all models used by SocioRAG."""
    from backend.app.core.singletons import get_logger, get_embedding_model, get_nlp
    from backend.app.core.config import get_config
    
    logger = get_logger()
    config = get_config()
    
    logger.info("🚀 Starting SocioRAG model preloading process...")
    logger.info(f"📁 Cache directory: {config.CACHE_DIR}")
    
    start_time = time.time()
    
    try:
        # 1. Load embedding model
        logger.info("📥 1/4 Loading embedding model...")
        embed_start = time.time()
        embedding_model = get_embedding_model()
        embed_time = time.time() - embed_start
        logger.info(f"✅ Embedding model loaded in {embed_time:.1f}s: {config.EMBEDDING_MODEL}")
        
        # Test embedding model
        test_embedding = embedding_model.encode("Test embedding")
        logger.info(f"🧪 Test embedding dimension: {len(test_embedding)}")
        
        # 2. Load spaCy model
        logger.info("📥 2/4 Loading spaCy model...")
        nlp_start = time.time()
        nlp = get_nlp()
        nlp_time = time.time() - nlp_start
        logger.info(f"✅ spaCy model loaded in {nlp_time:.1f}s: {config.SPACY_MODEL}")
        
        # Test spaCy model
        doc = nlp("Test spaCy processing")
        logger.info(f"🧪 spaCy test tokens: {[token.text for token in doc]}")
        
        # 3. Load translation model
        logger.info("📥 3/4 Loading translation model...")
        trans_start = time.time()
        try:
            from backend.app.retriever.language import _load_helsinki
            translation_loaded = _load_helsinki()
            trans_time = time.time() - trans_start
            if translation_loaded:
                logger.info(f"✅ Translation model loaded in {trans_time:.1f}s")
            else:
                logger.warning(f"⚠️ Translation model failed to load after {trans_time:.1f}s")
        except Exception as e:
            logger.error(f"❌ Error loading translation model: {e}")
        
        # 4. Load reranking model
        logger.info("📥 4/4 Loading reranking model...")
        rerank_start = time.time()
        try:
            from backend.app.retriever.vector import _get_reranker
            reranker = _get_reranker()
            rerank_time = time.time() - rerank_start
            if reranker is not None:
                logger.info(f"✅ Reranking model loaded in {rerank_time:.1f}s")
            else:
                logger.warning(f"⚠️ Reranking model failed to load after {rerank_time:.1f}s")
        except Exception as e:
            logger.error(f"❌ Error loading reranking model: {e}")
        
        total_time = time.time() - start_time
        logger.info(f"🎉 Model preloading completed in {total_time:.1f}s!")
        
        # Display cache information
        try:
            cache_size = sum(f.stat().st_size for f in config.CACHE_DIR.rglob('*') if f.is_file())
            cache_size_mb = cache_size / (1024 * 1024)
            logger.info(f"📊 Total cache size: {cache_size_mb:.1f} MB")
        except Exception as e:
            logger.warning(f"Could not calculate cache size: {e}")
        
        logger.info("🚀 Future SocioRAG startups will be much faster!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during model preloading: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_model_cache():
    """Check if models are already cached."""
    from backend.app.core.config import get_config
    from backend.app.core.singletons import get_logger
    
    config = get_config()
    logger = get_logger()
    
    if not config.CACHE_DIR.exists():
        logger.info("📭 No model cache found")
        return False
    
    # Check for key cache files
    cache_indicators = [
        config.SENTENCE_TRANSFORMERS_CACHE_DIR,
        config.TRANSFORMERS_CACHE_DIR,
        config.HF_CACHE_DIR
    ]
    
    cached_models = 0
    for cache_dir in cache_indicators:
        if cache_dir.exists() and any(cache_dir.iterdir()):
            cached_models += 1
    
    if cached_models > 0:
        try:
            cache_size = sum(f.stat().st_size for f in config.CACHE_DIR.rglob('*') if f.is_file())
            cache_size_mb = cache_size / (1024 * 1024)
            logger.info(f"📊 Found existing model cache: {cache_size_mb:.1f} MB")
            return True
        except Exception:
            logger.info("📊 Found existing model cache")
            return True
    
    return False

if __name__ == "__main__":
    print("🔧 SocioRAG Model Preloader")
    print("=" * 40)
    
    # Check if already cached
    if check_model_cache():
        print("✅ Models appear to be already cached!")
        response = input("🤔 Do you want to reload them anyway? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("👋 Skipping model preloading")
            sys.exit(0)
    
    # Preload models
    success = preload_all_models()
    
    if success:
        print("\n🎉 Model preloading completed successfully!")
        print("🚀 Your next SocioRAG startup will be much faster!")
        sys.exit(0)
    else:
        print("\n❌ Model preloading failed!")
        print("⚠️ Check the logs for more details")
        sys.exit(1)
