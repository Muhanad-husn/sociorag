"""Custom embedding model for semantic chunking."""

from sentence_transformers import SentenceTransformer
from llama_index.core.base.embeddings.base import BaseEmbedding
from pydantic import Field
from typing import List, Optional
import numpy as np

from backend.app.core.singletons import get_logger

logger = get_logger()


class SemanticEmbedding(BaseEmbedding):
    """Custom embedding model for semantic chunking."""
    
    model: SentenceTransformer = Field(default=None)
    max_length: Optional[int] = Field(default=512)
    normalize: bool = Field(default=True)
    
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        max_length: Optional[int] = 512,
        normalize: bool = True,
        cache_folder: Optional[str] = None,
        **kwargs
    ):
        super().__init__(model_name=model_name, **kwargs)
        self.model = SentenceTransformer(model_name, cache_folder=cache_folder)
        self.max_length = max_length
        self.normalize = normalize
        logger.info(f"Initialized SemanticEmbedding with model: {model_name}")
    
    def _get_text_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text."""
        embedding = self.model.encode(text, normalize_embeddings=self.normalize)
        return embedding.tolist()
    
    def _get_query_embedding(self, query: str) -> List[float]:
        """Get embedding for a query (same as text embedding)."""
        return self._get_text_embedding(query)
    
    def get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts."""
        embeddings = self.model.encode(texts, normalize_embeddings=self.normalize)
        return embeddings.tolist()
    
    async def _aget_text_embedding(self, text: str) -> List[float]:
        """Async version of _get_text_embedding."""
        return self._get_text_embedding(text)
    
    async def _aget_query_embedding(self, query: str) -> List[float]:
        """Async version of _get_query_embedding."""
        return self._get_query_embedding(query)
    
    async def aget_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Async version of get_text_embeddings."""
        return self.get_text_embeddings(texts)
