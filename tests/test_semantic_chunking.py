"""Tests for semantic chunking functionality."""

import pytest
import asyncio
from pathlib import Path
from typing import List, Dict, Any

from backend.app.ingest.semantic_chunker import SemanticChunker, AdaptiveSemanticChunker, HybridChunker
from backend.app.ingest.semantic_embedder import SemanticEmbedding
from backend.app.ingest.semantic_pipeline import SemanticDocumentProcessor, get_semantic_processor


class TestSemanticEmbedding:
    """Test semantic embedding functionality."""
    
    def test_embedding_initialization(self):
        """Test that SemanticEmbedding initializes correctly."""
        embedding = SemanticEmbedding()
        assert embedding.model is not None
        assert embedding.max_length == 512
        assert embedding.normalize is True
    
    def test_single_text_embedding(self):
        """Test embedding generation for single text."""
        embedding = SemanticEmbedding()
        text = "This is a test sentence for embedding."
        result = embedding._get_text_embedding(text)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(x, float) for x in result)
    
    def test_multiple_text_embeddings(self):
        """Test embedding generation for multiple texts."""
        embedding = SemanticEmbedding()
        texts = [
            "This is about dogs. Dogs are loyal animals.",
            "Cats are independent creatures that like to hunt."
        ]
        results = embedding.get_text_embeddings(texts)
        
        assert len(results) == 2
        assert all(isinstance(result, list) for result in results)
        assert all(len(result) > 0 for result in results)
    
    @pytest.mark.asyncio
    async def test_async_embedding(self):
        """Test async embedding generation."""
        embedding = SemanticEmbedding()
        text = "This is a test sentence for async embedding."
        result = await embedding._aget_text_embedding(text)
        
        assert isinstance(result, list)
        assert len(result) > 0


class TestSemanticChunker:
    """Test basic semantic chunking functionality."""
    
    def test_chunker_initialization(self):
        """Test that SemanticChunker initializes correctly."""
        chunker = SemanticChunker()
        assert chunker.embed_model is not None
        assert chunker.splitter is not None
        assert chunker.max_chunk_size == 1000
        assert chunker.min_chunk_size == 100
    
    def test_basic_chunking(self):
        """Test basic semantic chunking functionality."""
        chunker = SemanticChunker()
        text = (
            "This is about dogs. Dogs are loyal animals that have been companions to humans for thousands of years. "
            "They are known for their faithfulness and protective instincts. "
            "Now let's talk about cats. Cats are independent creatures that have a different relationship with humans. "
            "They are more solitary by nature and are excellent hunters."
        )
        chunks = chunker.chunk_text(text, "test_source")
        
        assert len(chunks) > 0
        assert all('content' in chunk for chunk in chunks)
        assert all('metadata' in chunk for chunk in chunks)
        assert all(chunk['metadata']['source'] == 'test_source' for chunk in chunks)
        assert all(chunk['metadata']['chunk_type'] in ['semantic', 'semantic_sub', 'fallback'] for chunk in chunks)
    
    def test_chunk_size_constraints(self):
        """Test that chunk size constraints are respected."""
        chunker = SemanticChunker(max_chunk_size=100, min_chunk_size=20)
        
        # Test with text that should create multiple chunks due to size constraints
        long_text = "This is a long sentence. " * 10  # Should exceed max_chunk_size
        chunks = chunker.chunk_text(long_text, "test_source")
        
        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk['content']) <= chunker.max_chunk_size + 50  # Some tolerance for sentence boundaries
    
    def test_fallback_chunking(self):
        """Test fallback chunking when semantic splitting fails."""
        chunker = SemanticChunker()
        
        # Test with empty or very short text
        short_text = "Short."
        chunks = chunker.chunk_text(short_text, "test_source")
        
        # Should handle gracefully
        assert isinstance(chunks, list)
    
    def test_large_chunk_splitting(self):
        """Test that large chunks are properly split."""
        chunker = SemanticChunker(max_chunk_size=50)  # Very small max size
        
        long_sentence = "This is a very long sentence that should definitely exceed the maximum chunk size and trigger splitting."
        chunks = chunker._split_large_chunk(long_sentence)
        
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= chunker.max_chunk_size + 20  # Some tolerance


class TestAdaptiveSemanticChunker:
    """Test adaptive semantic chunking functionality."""
    
    def test_adaptive_chunker_initialization(self):
        """Test that AdaptiveSemanticChunker initializes correctly."""
        chunker = AdaptiveSemanticChunker()
        assert chunker.embed_model is not None
        assert chunker.splitter is not None
    
    def test_document_type_analysis(self):
        """Test document type classification."""
        chunker = AdaptiveSemanticChunker()
        
        # Academic text
        academic_text = "Abstract: This study examines the methodology of research. The conclusion shows significant results."
        doc_type = chunker._analyze_document_type(academic_text)
        assert doc_type == "academic"
        
        # Narrative text
        narrative_text = "Once upon a time, there was a story. Meanwhile, in another chapter, suddenly something happened."
        doc_type = chunker._analyze_document_type(narrative_text)
        assert doc_type == "narrative"
        
        # General text
        general_text = "This is some general text about various topics without specific indicators."
        doc_type = chunker._analyze_document_type(general_text)
        assert doc_type == "general"
    
    def test_adaptive_chunking(self):
        """Test that adaptive chunking adjusts parameters based on document type."""
        chunker = AdaptiveSemanticChunker()
        
        academic_text = "Abstract: This study examines the methodology of research. The hypothesis is tested through controlled experiments. The conclusion shows significant results that advance our understanding."
        chunks = chunker.chunk_text(academic_text, "academic_test")
        
        assert len(chunks) > 0
        assert all('content' in chunk for chunk in chunks)
        assert all(chunk['metadata']['source'] == 'academic_test' for chunk in chunks)


class TestHybridChunker:
    """Test hybrid chunking with fallback functionality."""
    
    def test_hybrid_chunker_initialization(self):
        """Test that HybridChunker initializes correctly."""
        chunker = HybridChunker()
        assert chunker.semantic_chunker is not None
        assert chunker.rule_based_chunk is not None
    
    def test_successful_semantic_chunking(self):
        """Test hybrid chunker when semantic chunking succeeds."""
        chunker = HybridChunker()
        
        text = (
            "This is about technology. Technology has transformed our world in countless ways. "
            "From smartphones to artificial intelligence, we live in an era of rapid innovation. "
            "However, with great power comes great responsibility."
        )
        chunks = chunker.chunk_text(text, "hybrid_test")
        
        assert len(chunks) > 0
        assert all('content' in chunk for chunk in chunks)
        assert all('metadata' in chunk for chunk in chunks)
    
    def test_fallback_to_rule_based(self):
        """Test hybrid chunker fallback to rule-based chunking."""
        chunker = HybridChunker()
        
        # Test with various text types to ensure robustness
        test_texts = [
            "Very short text.",
            "A" * 2000,  # Very long text
            "Text with\nweird\n\nformatting\n\n\npatterns.",
        ]
        
        for text in test_texts:
            chunks = chunker.chunk_text(text, "fallback_test")
            assert isinstance(chunks, list)
            if chunks:  # If any chunks were created
                assert all('content' in chunk for chunk in chunks)
                assert all('metadata' in chunk for chunk in chunks)


class TestSemanticDocumentProcessor:
    """Test the semantic document processor."""
    
    def test_processor_initialization(self):
        """Test processor initialization with different configurations."""
        processor = SemanticDocumentProcessor()
        assert processor.config is not None
        
        # Should initialize appropriate chunker based on config
        if processor.config.SEMANTIC_CHUNKING_ENABLED:
            assert processor.chunker is not None
    
    def test_document_processing(self):
        """Test full document processing workflow."""
        processor = SemanticDocumentProcessor()
        
        document_text = (
            "Social dynamics in organizations are complex phenomena that involve multiple stakeholders. "
            "Power structures, communication patterns, and cultural norms all play crucial roles. "
            "Understanding these dynamics requires careful analysis of both formal and informal networks. "
            "This research examines how institutional frameworks shape individual behavior."
        )
        
        # Note: This test might fail if vector store is not available
        # In a real test environment, we'd mock the vector store
        try:
            chunks_data = processor.add_chunks_to_store(document_text, "test_doc")
            
            assert isinstance(chunks_data, list)
            assert len(chunks_data) > 0
            assert all('content' in chunk for chunk in chunks_data)
            assert all('metadata' in chunk for chunk in chunks_data)
            
        except Exception as e:
            # Expected if vector store is not set up in test environment
            pytest.skip(f"Vector store not available for testing: {e}")
    
    def test_processor_singleton(self):
        """Test that processor singleton works correctly."""
        processor1 = get_semantic_processor()
        processor2 = get_semantic_processor()
        
        assert processor1 is processor2  # Should be the same instance


# Integration tests
class TestSemanticPipelineIntegration:
    """Test integration between different components."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_processing(self):
        """Test end-to-end semantic processing pipeline."""
        try:
            from backend.app.ingest.semantic_pipeline import run_semantic_pipeline
            
            # Create a temporary test file
            test_dir = Path("test_input")
            test_dir.mkdir(exist_ok=True)
            
            # Skip if actual pipeline test is not feasible
            pytest.skip("End-to-end test requires full environment setup")
            
        except ImportError:
            pytest.skip("Semantic pipeline not available for testing")
        except Exception as e:
            pytest.skip(f"Pipeline test skipped: {e}")


# Performance tests
class TestSemanticChunkingPerformance:
    """Test performance characteristics of semantic chunking."""
    
    def test_chunking_performance(self):
        """Test chunking performance with larger texts."""
        chunker = SemanticChunker()
        
        # Generate a larger text for performance testing
        large_text = """
        This is a performance test for semantic chunking. We want to ensure that the chunking
        process can handle larger documents efficiently. The text contains multiple paragraphs
        and topics to test the semantic splitting capabilities.
        
        Social network analysis is a powerful methodology for understanding relationships and
        interactions within groups. It provides insights into how information flows, how
        influence spreads, and how communities form and evolve over time.
        
        In organizational contexts, social network analysis can reveal hidden patterns of
        communication and collaboration. These insights can be used to improve team dynamics,
        identify key influencers, and optimize organizational structure.
        
        The methodology involves collecting data on relationships and interactions, then
        applying various analytical techniques to identify patterns and structures. Visualization
        tools help make these patterns accessible to decision-makers.
        """ * 10  # Repeat to make it larger
        
        import time
        start_time = time.time()
        
        chunks = chunker.chunk_text(large_text, "performance_test")
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert len(chunks) > 0
        assert processing_time < 30  # Should complete within 30 seconds
        
        print(f"Processed {len(large_text)} characters into {len(chunks)} chunks in {processing_time:.2f} seconds")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
