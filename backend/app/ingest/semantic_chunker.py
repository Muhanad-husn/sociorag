"""Enhanced semantic chunking using embedding similarity analysis."""

from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.core import Document
from llama_index.core.schema import Node
from typing import List, Dict, Any
import logging
import re

from backend.app.core.singletons import get_logger
from backend.app.core.config import get_config
from .semantic_embedder import SemanticEmbedding

logger = get_logger()
config = get_config()


class SemanticChunker:
    """Advanced semantic chunking using embedding similarity analysis."""
    
    def __init__(
        self,
        model_name: str = None,
        buffer_size: int = 1,
        breakpoint_percentile_threshold: int = 85,
        max_chunk_size: int = 3000,
        min_chunk_size: int = 100
    ):
        # Use config defaults if not specified
        self.model_name = model_name or config.RERANKER_MODEL
        self.buffer_size = buffer_size
        self.breakpoint_percentile_threshold = breakpoint_percentile_threshold
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        
        # Initialize embedding model
        self.embed_model = SemanticEmbedding(
            model_name=self.model_name,
            max_length=512,
            normalize=True
        )
        
        # Initialize semantic splitter
        self.splitter = SemanticSplitterNodeParser(
            buffer_size=self.buffer_size,
            breakpoint_percentile_threshold=self.breakpoint_percentile_threshold,
            embed_model=self.embed_model
        )
        
        logger.info(f"Initialized SemanticChunker with threshold: {self.breakpoint_percentile_threshold}")
    
    def chunk_text(self, text: str, source: str = "unknown") -> List[Dict[str, Any]]:
        """
        Chunk text using semantic similarity analysis.
        
        Args:
            text: Text to chunk
            source: Source identifier for metadata
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        logger.info(f"Starting semantic chunking for text of length {len(text)}")
        
        # Create document
        document = Document(text=text)
        
        # Get semantic nodes
        try:
            nodes = self.splitter.get_nodes_from_documents([document])
        except Exception as e:
            logger.error(f"Semantic splitting failed: {e}")
            # Fallback to simple sentence splitting
            return self._fallback_chunk(text, source)
        
        # Convert to chunk format
        chunks = []
        for i, node in enumerate(nodes):
            content = node.get_content()
            
            # Skip chunks that are too small or too large
            if len(content) < self.min_chunk_size:
                logger.debug(f"Skipping chunk {i}: too small ({len(content)} chars)")
                continue
                
            if len(content) > self.max_chunk_size:
                logger.debug(f"Splitting large chunk {i}: {len(content)} chars")
                # Fall back to sentence splitting for oversized chunks
                sub_chunks = self._split_large_chunk(content)
                for j, sub_chunk in enumerate(sub_chunks):
                    chunks.append({
                        'content': sub_chunk,
                        'metadata': {
                            'source': source,
                            'chunk_index': f"{i}_{j}",
                            'chunk_type': 'semantic_sub',
                            'char_count': len(sub_chunk),
                            'semantic_score': None  # Sub-chunks don't have semantic scores
                        }
                    })
            else:
                chunks.append({
                    'content': content,
                    'metadata': {
                        'source': source,
                        'chunk_index': i,
                        'chunk_type': 'semantic',
                        'char_count': len(content),
                        'semantic_score': getattr(node, 'semantic_score', None)
                    }
                        })
        
        logger.info(f"Created {len(chunks)} semantic chunks")
        return chunks
    
    def _split_large_chunk(self, text: str) -> List[str]:
        """Fall back to sentence splitting for oversized chunks."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # If we only get one sentence that's too long, split by words
        if len(sentences) == 1 and len(text) > self.max_chunk_size:
            words = text.split()
            chunks = []
            current_chunk = ""
            
            for word in words:
                if len(current_chunk) + len(word) + 1 <= self.max_chunk_size:
                    current_chunk += word + " "
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = word + " "
            
            if current_chunk:
                chunks.append(current_chunk.strip())
                
            return chunks
        
        # Normal sentence-based splitting
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= self.max_chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks
    
    def _fallback_chunk(self, text: str, source: str) -> List[Dict[str, Any]]:
        """Fallback to simple chunking when semantic splitting fails."""
        logger.warning("Using fallback chunking method")
        chunks = self._split_large_chunk(text)
        
        return [
            {
                'content': chunk,
                'metadata': {
                    'source': source,
                    'chunk_index': i,
                    'chunk_type': 'fallback',
                    'char_count': len(chunk),
                    'semantic_score': None
                }
            }
            for i, chunk in enumerate(chunks)
        ]


class AdaptiveSemanticChunker(SemanticChunker):
    """Adaptive chunker that adjusts parameters based on document characteristics."""
    
    def chunk_text(self, text: str, source: str = "unknown") -> List[Dict[str, Any]]:
        # Analyze document characteristics
        doc_type = self._analyze_document_type(text)
        
        # Adjust parameters based on document type
        if doc_type == "academic":
            self.splitter.breakpoint_percentile_threshold = 75  # More sensitive
            self.splitter.buffer_size = 2
        elif doc_type == "narrative":
            self.splitter.breakpoint_percentile_threshold = 90  # Less sensitive
            self.splitter.buffer_size = 1
        else:  # general
            self.splitter.breakpoint_percentile_threshold = 85
            self.splitter.buffer_size = 1
        
        logger.info(f"Adapted chunking for {doc_type} document type")
        return super().chunk_text(text, source)
    
    def _analyze_document_type(self, text: str) -> str:
        """Simple document type classification."""
        academic_indicators = ["abstract", "methodology", "conclusion", "references", "hypothesis"]
        narrative_indicators = ["chapter", "once upon", "meanwhile", "suddenly", "story"]
        
        text_lower = text.lower()
        academic_score = sum(1 for indicator in academic_indicators if indicator in text_lower)
        narrative_score = sum(1 for indicator in narrative_indicators if indicator in text_lower)
        
        if academic_score > narrative_score and academic_score > 2:
            return "academic"
        elif narrative_score > academic_score and narrative_score > 1:
            return "narrative"
        else:
            return "general"


class HybridChunker:
    """Hybrid chunker that falls back to rule-based chunking if semantic fails."""
    
    def __init__(self, **kwargs):
        self.semantic_chunker = AdaptiveSemanticChunker(**kwargs)
        # Import here to avoid circular imports
        from .chunker import chunk_page
        self.rule_based_chunk = chunk_page
    
    def chunk_text(self, text: str, source: str = "unknown") -> List[Dict[str, Any]]:
        """Try semantic chunking first, fall back to rule-based if it fails."""
        try:
            # Try semantic chunking first
            chunks = self.semantic_chunker.chunk_text(text, source)
            if chunks:  # If we got valid chunks
                return chunks
        except Exception as e:
            logger.warning(f"Semantic chunking failed, falling back to rule-based: {e}")
        
        # Fall back to rule-based chunking
        rule_chunks = self.rule_based_chunk(text)
        return [
            {
                'content': chunk,
                'metadata': {
                    'source': source,
                    'chunk_index': i,
                    'chunk_type': 'rule_based',
                    'char_count': len(chunk),
                    'semantic_score': None
                }
            }
            for i, chunk in enumerate(rule_chunks)
        ]
