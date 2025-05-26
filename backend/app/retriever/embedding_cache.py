"""
Embedding cache module for SocioGraph.

This module provides caching functionality for embedding operations to improve performance
by avoiding redundant embedding calculations for frequently used texts.
"""

import time
from typing import Dict, List, Union, Tuple, Optional
import hashlib
import threading

# Type for cache entries: (embedding, timestamp)
CacheEntryType = Tuple[Union[List[float], List[List[float]]], float]

class EmbeddingCache:
    """Thread-safe cache for embeddings with time-based expiration."""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """Initialize the embedding cache.
        
        Args:
            max_size: Maximum number of entries in the cache (default: 1000)
            ttl_seconds: Time to live in seconds for cache entries (default: 1 hour)
        """
        self._cache: Dict[str, CacheEntryType] = {}
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        
    def _get_key(self, text: Union[str, List[str]]) -> str:
        """Generate a cache key for the given text.
        
        Args:
            text: Text or list of texts to generate a key for
            
        Returns:
            A unique hash string for the text
        """
        if isinstance(text, list):
            # For list of texts, concatenate with a special separator
            text_to_hash = "|||".join(text)
        else:
            text_to_hash = text
            
        # Generate MD5 hash of the text
        return hashlib.md5(text_to_hash.encode('utf-8')).hexdigest()
        
    def get(self, text: Union[str, List[str]]) -> Optional[Union[List[float], List[List[float]]]]:
        """Get an embedding from the cache if it exists and is not expired.
        
        Args:
            text: Text or list of texts to get embedding for
            
        Returns:
            Cached embedding or None if not found or expired
        """
        key = self._get_key(text)
        
        with self._lock:
            if key in self._cache:
                embedding, timestamp = self._cache[key]
                
                # Check if entry has expired
                if time.time() - timestamp <= self._ttl_seconds:
                    return embedding
                else:
                    # Remove expired entry
                    del self._cache[key]
                    
        return None
        
    def set(self, text: Union[str, List[str]], 
            embedding: Union[List[float], List[List[float]]]) -> None:
        """Store an embedding in the cache.
        
        Args:
            text: Text or list of texts the embedding is for
            embedding: The embedding vector(s) to store
        """
        key = self._get_key(text)
        timestamp = time.time()
        
        with self._lock:
            # If cache is full, remove oldest entry
            if len(self._cache) >= self._max_size and key not in self._cache:
                oldest_key = min(self._cache.keys(), 
                                key=lambda k: self._cache[k][1])
                del self._cache[oldest_key]
                
            # Store the new entry
            self._cache[key] = (embedding, timestamp)
            
    def clear(self) -> None:
        """Clear all entries from the cache."""
        with self._lock:
            self._cache.clear()
            
    def cleanup(self) -> int:
        """Remove expired entries from the cache.
        
        Returns:
            Number of entries removed
        """
        now = time.time()
        expired_keys = []
        
        with self._lock:
            # Identify expired keys
            for key, (_, timestamp) in self._cache.items():
                if now - timestamp > self._ttl_seconds:
                    expired_keys.append(key)
                    
            # Remove expired keys
            for key in expired_keys:
                del self._cache[key]
                
        return len(expired_keys)
        
    def size(self) -> int:
        """Get the current number of entries in the cache.
        
        Returns:
            Number of entries in the cache
        """
        with self._lock:
            return len(self._cache)
            
    def stats(self) -> Dict[str, int]:
        """Get statistics about the cache.
        
        Returns:
            Dictionary with statistics about the cache
        """
        now = time.time()
        with self._lock:
            total = len(self._cache)
            expired = sum(1 for _, timestamp in self._cache.values() 
                         if now - timestamp > self._ttl_seconds)
                         
        return {
            "total_entries": total,
            "expired_entries": expired,
            "active_entries": total - expired,
            "max_size": self._max_size
        }

# Global instance of the embedding cache
_embedding_cache = EmbeddingCache()

def get_embedding_cache() -> EmbeddingCache:
    """Get the global embedding cache instance.
    
    Returns:
        Global embedding cache instance
    """
    return _embedding_cache
