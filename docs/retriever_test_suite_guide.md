# Retriever Module Test Suite Guide

## Overview

This document provides a guide to the test suite for the SocioGraph retriever module. The test suite verifies the functionality of the vector retrieval, embedding cache, similarity calculations, and the full retrieval pipeline.

## Test Files

### `test_embedding_cache.py`

Tests the embedding cache functionality:
- `test_cache_hit()`: Verifies that embeddings are correctly cached and retrieved
- `test_cache_batch()`: Tests batch embedding caching
- `test_cache_expiration()`: Ensures cache entries expire after TTL
- `test_cache_cleanup()`: Tests that cleanup removes expired entries

### `test_embedding_singleton_integration.py`

Tests the integration of EmbeddingSingleton across different components:
- `test_vector_retrieval()`: Tests vector retrieval with text and embedding queries
- `test_reranking(chunks)`: Tests the reranking functionality
- `test_graph_retrieval()`: Tests the graph retrieval functionality
- `test_full_pipeline()`: Tests the complete retrieval pipeline
- `test_similarity_functions()`: Tests various similarity calculation functions

### `test_enhanced_vector_utils.py`

Tests the enhanced vector utilities:
- `test_embedding_singleton()`: Tests basic embedding functionality
- `test_vector_extraction()`: Tests vector extraction from different formats
- `test_similarity_calculation()`: Tests similarity calculations with different inputs
- `test_batch_similarity()`: Tests batch similarity performance
- `test_integration()`: Tests integration with document reranking

### `test_similarity_functions.py`

Tests similarity function implementations:
- `test_similarity_functions()`: Tests various similarity functions
- `test_with_different_embedding_formats()`: Tests handling of different embedding formats

### `test_sqlite_vec_utils.py`

Tests SQLite vector utilities:
- `test_embedding_conversion()`: Tests embedding conversion for storage
- `test_entity_search()`: Tests entity search functionality

## Test Fixtures

The test suite uses the following fixtures (defined in `conftest.py`):
- `chunks`: Provides text chunks for reranking tests

## Running the Tests

To run all retriever tests:
```bash
python -m tests.retriever
```

To run a specific test file:
```bash
python -m pytest tests/retriever/test_embedding_cache.py
```

To run a specific test:
```bash
python -m pytest tests/retriever/test_embedding_cache.py::test_cache_hit
```

## Test Structure Best Practices

1. **Use assertions, not returns**: Test functions should use `assert` statements to validate behavior, not return values.
   ```python
   # Good
   assert len(chunks) > 0, "Should retrieve at least one chunk"
   
   # Bad
   return chunks
   ```

2. **Use fixtures for shared resources**: Use pytest fixtures for resources needed by multiple tests.
   ```python
   @pytest.fixture
   def chunks():
       """Fixture to provide chunks for reranking tests."""
       query_text = "What are the impacts of climate change on biodiversity?"
       chunks = retrieve_chunks(query_text=query_text)
       return chunks
   ```

3. **Document test functions**: Use docstrings to explain what each test is verifying.
   ```python
   def test_cache_hit():
       """Test that embeddings are correctly cached and retrieved."""
       # Test implementation...
   ```

4. **Log useful information**: Use logging to provide context when tests run.
   ```python
   logger.info(f"Retrieved {len(chunks)} chunks in {elapsed:.2f}s")
   ```

5. **Test both success and edge cases**: Ensure tests cover both normal operation and edge cases.

## Adding New Tests

When adding new tests to the retriever module:

1. Create a new test file with the naming pattern `test_*.py` if testing a new component
2. Add the standard imports and path setup at the top of the file
3. Define test functions following the naming pattern `test_*`
4. Use assertions to validate expected behavior
5. Add the test to the main block if manual execution is needed

## Conclusion

The retriever module test suite provides comprehensive coverage of the vector retrieval and embedding functionality. By following the established patterns and best practices, the test suite can be maintained and extended as the codebase evolves.
