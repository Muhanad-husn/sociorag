"""Unit tests for the retriever module."""

import time
import pytest

from backend.app.retriever import retrieve_context

@pytest.mark.parametrize("query", [
    "What is a knowledge graph?",
    "How do knowledge graphs help AI systems?",
    "ما هي الرسوم البيانية للمعرفة؟"  # Arabic: "What are knowledge graphs?"
])
def test_retrieval_pipeline(query):
    """Test the full retrieval pipeline."""
    start = time.time()
    
    # Call the retrieval pipeline
    result = retrieve_context(query)
    
    # Verify structure and content
    assert "lang" in result
    assert result["lang"] in {"en", "ar"}
    assert "query_en" in result
    assert "chunks" in result
    assert "triples" in result
    assert "context" in result
      # Verify context contents
    assert "merged_texts" in result["context"]
    assert isinstance(result["context"]["merged_texts"], list)
    
    # Performance check - increased time limit for first run and when fallbacks are used
    elapsed = time.time() - start
    assert elapsed < 10.0, f"Retrieval took too long: {elapsed:.2f}s"
    
    print(f"Retrieval completed in {elapsed:.2f}s")
    print(f"Retrieved {len(result['chunks'])} chunks and {len(result['triples'])} triples")
    print(f"Total context tokens: {result['context']['total_tokens']}")
    
    # Return a sample of the context for manual inspection
    return result["context"]["merged_texts"][:2] if result["context"]["merged_texts"] else []
