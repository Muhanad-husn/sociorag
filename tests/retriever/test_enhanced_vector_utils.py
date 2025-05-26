"""
Test script to verify the enhanced vector utilities and EmbeddingSingleton integration.

This script tests:
1. Basic embedding functionality
2. Similarity calculation with different input formats
3. Batch similarity performance
4. Integration with reranking
"""

import logging
import time
from scipy.spatial.distance import cosine
from backend.app.core.singletons import get_logger, embed_texts
from backend.app.retriever.vector_utils import (
    calculate_cosine_similarity,
    batch_similarity,
    text_similarity,
    extract_vector
)

# Set up logging
logger = get_logger()
logger.setLevel(logging.INFO)

class MockDocument:
    """Mock document class for testing reranking."""
    def __init__(self, content):
        self.page_content = content

def test_embedding_singleton():
    """Test basic embedding functionality."""
    logger.info("Testing basic embedding functionality...")
    
    # Test single text embedding
    text = "Climate change is a major global challenge"
    embedding = embed_texts(text)
    
    logger.info(f"Single text embedding shape: {len(embedding)}")
    assert isinstance(embedding, list), "Single embedding should be a list"
    assert isinstance(embedding[0], float), "Embedding values should be floats"
    
    # Test batch embedding
    texts = [
        "Climate change is a major global challenge",
        "Global warming is affecting the planet",
        "Artificial intelligence is transforming industries"
    ]
    
    embeddings = embed_texts(texts)
    logger.info(f"Batch embeddings shape: {len(embeddings)}x{len(embeddings[0])}")
    
    assert isinstance(embeddings, list), "Batch embeddings should be a list"
    assert isinstance(embeddings[0], list), "Each batch embedding should be a list"
    assert isinstance(embeddings[0][0], float), "Embedding values should be floats"
    
    logger.info("✓ Basic embedding tests passed")

def test_vector_extraction():
    """Test vector extraction function."""
    logger.info("Testing vector extraction functionality...")
    
    # Test with single embedding
    text = "Climate change is a major global challenge"
    embedding = embed_texts(text)
    
    extracted = extract_vector(embedding)
    assert len(extracted) == len(embedding), "Extracted vector should have same length as original"
    
    # Test with batch embeddings
    texts = [
        "Climate change is a major global challenge",
        "Global warming is affecting the planet"
    ]
    embeddings = embed_texts(texts)
    
    extracted = extract_vector(embeddings)
    assert len(extracted) == len(embeddings[0]), "Extracted vector should have same length as first batch item"
    
    logger.info("✓ Vector extraction tests passed")

def test_similarity_calculation():
    """Test similarity calculation with different formats."""
    logger.info("Testing similarity calculation...")
    
    # Prepare test data
    texts = [
        "Climate change is a major global challenge",
        "Global warming is affecting the planet",
        "Artificial intelligence is transforming industries"
    ]
    
    # Get embeddings
    single_emb = embed_texts(texts[0])
    another_single_emb = embed_texts(texts[1])
    batch_embs = embed_texts(texts)
    
    # Test similarity between single embeddings
    sim1 = calculate_cosine_similarity(single_emb, another_single_emb)
    logger.info(f"Similarity between single embeddings: {sim1:.6f}")
    
    # Test similarity between single and batch embeddings
    sim2 = calculate_cosine_similarity(single_emb, batch_embs)
    logger.info(f"Similarity between single and batch embeddings: {sim2:.6f}")
    
    # Test similarity between batch and single embeddings
    sim3 = calculate_cosine_similarity(batch_embs, single_emb)
    logger.info(f"Similarity between batch and single embeddings: {sim3:.6f}")
    
    # Calculate with scipy for verification
    scipy_sim = 1 - cosine(single_emb, another_single_emb)
    logger.info(f"SciPy similarity for verification: {scipy_sim:.6f}")
    
    assert abs(sim1 - scipy_sim) < 1e-5, "Similarity calculation should match scipy"
    
    logger.info("✓ Similarity calculation tests passed")

def test_batch_similarity():
    """Test batch similarity performance."""
    logger.info("Testing batch similarity performance...")
    
    # Prepare test data
    query = "Climate change impacts"
    docs = [
        "Climate change is a major global challenge",
        "Global warming is affecting the planet",
        "Artificial intelligence is transforming industries",
        "Machine learning algorithms can predict patterns",
        "Renewable energy sources are becoming more affordable"
    ]
    
    # Get embeddings
    query_emb = embed_texts(query)
    doc_embs = embed_texts(docs)
      # Test batch similarity
    start = time.time()
    similarities = batch_similarity(query_emb, doc_embs)
    elapsed = time.time() - start
    
    logger.info(f"Batch similarity took {elapsed:.6f}s for {len(docs)} documents")
    logger.info(f"Similarities: {[f'{s:.4f}' for s in similarities]}")
    
    # Verify results are reasonable
    assert len(similarities) == len(docs), "Should have one similarity score per document"
    assert all(0 <= s <= 1 for s in similarities), "Similarities should be between 0 and 1"
    
    # Test text_similarity which combines embedding and similarity
    text_sims = text_similarity(query, docs)
    
    logger.info(f"Text similarities: {[f'{s:.4f}' for s in text_sims]}")
    assert len(text_sims) == len(docs), "Should return one similarity per document"
    
    # Compare with individual calculations
    individual_sims = []
    for doc_emb in doc_embs:
        sim = calculate_cosine_similarity(query_emb, doc_emb)
        individual_sims.append(sim)
    
    # Verify batch results match individual calculations
    for i in range(len(similarities)):
        assert abs(similarities[i] - individual_sims[i]) < 1e-5, "Batch similarity should match individual calculations"
    
    logger.info("✓ Batch similarity tests passed")

def test_integration():
    """Test integration with document reranking."""
    logger.info("Testing integration with document reranking...")
    
    # Create mock documents
    docs = [
        MockDocument("Climate change is a major global challenge"),
        MockDocument("Global warming is affecting the planet"),
        MockDocument("Artificial intelligence is transforming industries"),
        MockDocument("Machine learning algorithms can predict patterns"),
        MockDocument("Renewable energy sources are becoming more affordable")
    ]
    
    # Test text similarity with mock documents
    query = "Climate change impacts"
    doc_texts = [d.page_content for d in docs]
    
    # Get similarities
    similarities = text_similarity(query, doc_texts)
    
    # Create ranked documents
    ranked = sorted(zip(docs, similarities), key=lambda x: x[1], reverse=True)
    ranked_docs = [doc for doc, _ in ranked]
    
    # Verify ranking makes sense
    logger.info("Ranked documents:")
    for i, (doc, sim) in enumerate(ranked):
        logger.info(f"{i+1}. {doc.page_content} ({sim:.4f})")
    
    # The first result should be about climate change
    assert "climate" in ranked_docs[0].page_content.lower() or "warming" in ranked_docs[0].page_content.lower(), \
        "First result should be about climate"
    
    logger.info("✓ Integration tests passed")

if __name__ == "__main__":
    logger.info("Starting enhanced vector utilities tests...")
    
    # Run tests
    test_embedding_singleton()
    test_vector_extraction()
    test_similarity_calculation()
    test_batch_similarity()
    test_integration()
    
    logger.info("All tests completed successfully!")



