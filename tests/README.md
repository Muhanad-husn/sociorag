# SocioRAG Testing Framework

This directory contains comprehensive tests for all SocioRAG functionalities, organized in a unified structure.

> **📚 For detailed testing guides, see [Frontend Testing Guide](../docs/guides/frontend_testing_guide.md)**

## Directory Structure

```text
tests/
├── backend/           # Backend API and core functionality tests
├── frontend/          # Frontend and UI tests
├── retriever/         # Vector search and retrieval tests
├── ingest/           # Data ingestion and processing tests
├── scripts/          # Script and utility tests
├── data/             # Test data files (JSON, TXT, etc.)
└── README.md         # This file
```

## Test Categories

### Backend Tests (`backend/`)

- **test_config.py** - Configuration system validation
- **test_admin_api.py** - Admin API endpoints
- **test_llm_singleton.py** - Language model singleton
- **test_retriever.py** - Retrieval system
- **test_singletons.py** - Core singleton infrastructure
- **test_translation.py** - Translation functionality

### Retriever Tests (`retriever/`)

- **test_embedding.py** - Embedding generation
- **test_embedding_cache.py** - Embedding caching system
- **test_embedding_singleton_integration.py** - Embedding singleton integration
- **test_enhanced_reranking.py** - Enhanced reranking algorithms
- **test_enhanced_vector_utils.py** - Vector utility functions
- **test_similarity_functions.py** - Similarity calculation functions
- **test_sqlite_vec_utils.py** - SQLite vector utilities

### Frontend Tests (`frontend/`)

- **test_history_frontend.html** - Complete history API frontend testing

### Ingest Tests (`ingest/`)

- **test_reset_corpus.py** - Corpus reset functionality

### Core Tests (root level)

- **test_enhanced_entity_extraction.py** - Enhanced entity extraction with retry and caching
- **test_pdf_generation_workflow.py** - PDF generation workflow

### Scripts Tests (`scripts/`)

- **test_logging.py** - Enhanced logging system

### Test Data (`data/`)

- **test_request.json** - Sample API request
- **test_stream_request.json** - Sample streaming request
- **test_queries.txt** - Test query samples

## Running Tests

### Python Tests

Run all Python tests:

```bash
pytest tests/ -v
```

Run specific test category:

```bash
pytest tests/backend/ -v
pytest tests/retriever/ -v
```

Run integration tests:

```bash
pytest tests/ -m integration -v
```

### Frontend Tests

Open HTML test files in a browser while the backend is running:

```bash
# Start the backend first
python -m uvicorn backend.app.main:app --reload

# Then open in browser:
# file:///d:/sociorag/tests/frontend/test_history_frontend.html
```

## Test Data Management

Test data files are consolidated in the `data/` directory:

- JSON files for API request testing
- Text files for query testing
- Configuration files for test scenarios

## Environment Variables

For testing with custom configurations:

- `SOCIORAG_API_URL`: Backend API URL (default: `http://127.0.0.1:8000`)
- `SOCIORAG_FRONTEND_URL`: Frontend URL (default: `http://localhost:5173`)

## Test Organization Principles

1. **Unified Structure**: All tests under `tests/` directory
2. **Categorized by Function**: Backend, frontend, retriever, etc.
3. **No Duplicates**: Superseded tests removed, enhanced versions kept
4. **Consistent Naming**: `test_` prefix for all test files
5. **Proper Documentation**: Each test category documented with purpose
