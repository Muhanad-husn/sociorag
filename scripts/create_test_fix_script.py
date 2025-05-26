"""
Create a script to manually fix the test files with pytest warnings.
"""

import os
import re
from pathlib import Path

def main():
    """Main function to create the manual fix script."""
    script_content = """
# Fix test files with pytest warnings
cd $PSScriptRoot\\..

# Make a backup of original files
Copy-Item tests\\retriever\\test_embedding_singleton_integration.py tests\\retriever\\test_embedding_singleton_integration.py.bak
Copy-Item tests\\retriever\\test_enhanced_vector_utils.py tests\\retriever\\test_enhanced_vector_utils.py.bak

# Fix test_embedding_singleton_integration.py
@'
\"\"\"
Test the extended EmbeddingSingleton integration.

This script tests the full integration of EmbeddingSingleton across different
components of the SocioGraph Phase 4 implementation.
\"\"\"

import sys
import time
import os
import pytest
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))


from backend.app.core.singletons import get_logger, embed_texts
from backend.app.retriever.pipeline import retrieve_context
from backend.app.retriever.vector import retrieve_chunks, rerank_chunks
from backend.app.retriever.graph import retrieve_triples
from backend.app.retriever.vector_utils import text_similarity, batch_similarity

# Initialize logger
logger = get_logger()

def test_vector_retrieval():
    \"\"\"Test the enhanced vector retrieval functionality.\"\"\"
    logger.info("Testing vector retrieval with text query...")
    
    # Test with text query
    query_text = "What are the impacts of climate change on biodiversity?"
    start_time = time.time()
    chunks = retrieve_chunks(query_text=query_text)
    elapsed = time.time() - start_time
    
    logger.info(f"Retrieved {len(chunks)} chunks in {elapsed:.2f}s using text query")
    
    # Test with embedding
    query_embedding = embed_texts(query_text)
    start_time = time.time()
    chunks2 = retrieve_chunks(query_emb=query_embedding)
    elapsed = time.time() - start_time
    
    logger.info(f"Retrieved {len(chunks2)} chunks in {elapsed:.2f}s using embedding")
    
    # Compare results
    logger.info(f"Text query and embedding query should give similar results: {len(chunks) == len(chunks2)}")
    
    # Assert that the chunks are valid
    assert len(chunks) > 0, "Should retrieve at least one chunk"
    assert all(hasattr(chunk, 'page_content') for chunk in chunks), "All chunks should have page_content"

def test_reranking(chunks):
    \"\"\"Test the reranking functionality.\"\"\"
    if not chunks:
        logger.warning("No chunks to rerank")
        return
        
    logger.info("Testing reranking...")
    
    query_text = "What are the impacts of climate change on biodiversity?"
    start_time = time.time()
    reranked_chunks = rerank_chunks(query_text, chunks)
    elapsed = time.time() - start_time
    
    logger.info(f"Reranked {len(reranked_chunks)} chunks in {elapsed:.2f}s")
    
    # Print first chunk for inspection
    if reranked_chunks:
        logger.info(f"First reranked chunk: {reranked_chunks[0].page_content[:150]}...")
        
    # Assert that the reranking worked
    assert len(reranked_chunks) > 0, "Should have at least one reranked chunk"

def test_graph_retrieval():
    \"\"\"Test the graph retrieval functionality.\"\"\"
    logger.info("Testing graph retrieval...")
    
    query_text = "What are the impacts of climate change on biodiversity?"
    start_time = time.time()
    triples = retrieve_triples(query_text)
    elapsed = time.time() - start_time
    
    logger.info(f"Retrieved {len(triples)} triples in {elapsed:.2f}s")
    
    # Print first few triples for inspection
    if triples:
        for i, triple in enumerate(triples[:3]):
            logger.info(f"Triple {i+1}: {triple['source_name']} {triple['relation_type']} {triple['target_name']}")
    
    # Assert that triples were found (or accept empty results if none match query)
    assert triples is not None, "Triples result should not be None"

def test_full_pipeline():
    \"\"\"Test the full retrieval pipeline.\"\"\"
    logger.info("Testing full retrieval pipeline...")
    
    query_text = "What are the impacts of climate change on biodiversity?"
    start_time = time.time()
    result = retrieve_context(query_text)
    elapsed = time.time() - start_time
    
    logger.info(f"Retrieved context in {elapsed:.2f}s")
    logger.info(f"Result contains {len(result['chunks'])} chunks and {len(result['triples'])} triples")
    
    # Check if context was merged properly
    context = result['context']
    logger.info(f"Context contains {len(context.get('merged_texts', []))} merged texts")
    
    # Assert that we got a valid response
    assert 'chunks' in result, "Result should contain chunks"
    assert 'context' in result, "Result should contain context"

def test_similarity_functions():
    \"\"\"Test the similarity functions.\"\"\"
    logger.info("Testing similarity functions...")
    
    texts = [
        "Climate change is affecting biodiversity",
        "Global warming impacts ecosystems",
        "Renewable energy reduces emissions",
        "Unrelated topic about sports"
    ]
    
    query = "How does climate change impact nature?"
    
    # Test text_similarity
    logger.info(f"Testing text_similarity with query: '{query}'")
    scores = text_similarity(query, texts)
    
    logger.info("Text similarity results:")
    for i, (text, score) in enumerate(zip(texts, scores)):
        logger.info(f"  {i+1}. {text} - Score: {score:.4f}")
    
    # Test batch_similarity
    logger.info("Testing batch_similarity...")
    query_embedding = embed_texts(query)
    doc_embeddings = embed_texts(texts)
    batch_scores = batch_similarity(query_embedding, doc_embeddings)
    
    logger.info("Batch similarity results:")
    for i, (text, score) in enumerate(zip(texts, batch_scores)):
        logger.info(f"  {i+1}. {text} - Score: {score:.4f}")
    
    # Assert that the scores are valid
    assert len(scores) == len(texts), "Should have one score per text"
    assert all(0 <= s <= 1 for s in scores), "Scores should be between 0 and 1"

if __name__ == "__main__":
    logger.info("Starting EmbeddingSingleton integration test...")
    
    # Test vector retrieval
    test_vector_retrieval()
    
    # We need to get chunks for testing reranking
    chunks = retrieve_chunks(query_text="What are the impacts of climate change on biodiversity?")
    
    # Test reranking with chunks
    test_reranking(chunks)
    
    # Test graph retrieval
    test_graph_retrieval()
    
    # Test similarity functions
    test_similarity_functions()
    
    # Test full pipeline
    test_full_pipeline()
    
    logger.info("EmbeddingSingleton integration test completed successfully!")
'@ | Set-Content -Path tests\\retriever\\test_embedding_singleton_integration.py

# Run the tests to verify fixes
Write-Host "Running tests to verify fixes..."
python -m tests.retriever

Write-Host "Test file fixes completed."
    """
    
    script_path = Path("d:/sociorag/scripts/fix_test_files_manually.ps1")
    script_path.write_text(script_content)
    
    print(f"Created fix script at {script_path}")
    print("Run this script to manually fix the test files with pytest warnings.")

if __name__ == "__main__":
    main()
