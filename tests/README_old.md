# SocioRAG Testing Framework

This directory contains comprehensive tests for all SocioRAG functionalities, organized in a unified structure.

> **📚 For detailed testing guides, see [Frontend Testing Guide](../docs/guides/frontend_testing_guide.md)**

## Directory Structure

```
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

### Frontend Tests  
Browser-based tests for frontend functionality (see `frontend/` directory).

### Backend API Tests
Integration tests for backend endpoints and functionality.

## Directory Structure

```
tests/
├── frontend/                   # Frontend HTML-based tests
│   ├── README.md              # Frontend testing documentation
│   ├── test_history_api.html  # Basic history API test
│   ├── debug_history_api.html # Debug and multi-method API test
│   └── complete_history_test.html # Comprehensive test suite
├── ingest/                    # Data ingestion tests
├── retriever/                 # Information retrieval tests
└── *.py                      # Python test modules
```

## Test Files

### test_pdf_generation_workflow.py

Comprehensive integration test for PDF generation user choice functionality.

**What it tests:**

- Backend API endpoints with `generate_pdf` parameter
- PDF generation enabled/disabled scenarios  
- Arabic language support with PDF options
- Both GET and POST API endpoints
- Complete workflow functionality

**Requirements:**

- Backend server must be running
- `requests` library must be installed
- Optional: Set environment variables for custom URLs

**Environment Variables:**

- `SOCIORAG_API_URL`: Backend API URL (default: `http://127.0.0.1:8000`)
- `SOCIORAG_FRONTEND_URL`: Frontend URL (default: `http://localhost:5173`)

**Usage:**

Run with Python directly:

```bash
python tests/test_pdf_generation_workflow.py
```

Run with pytest:

```bash
pytest tests/test_pdf_generation_workflow.py -v
```

Run only integration tests:

```bash
pytest tests/ -m integration -v
```

### Frontend Tests

See `frontend/README.md` for detailed information about HTML-based frontend tests.

**Quick Usage:**

1. Start backend and frontend servers
2. Open HTML test files in browser
3. Click test buttons to run validation
4. Check results and console output

## Test Markers

- `@pytest.mark.integration`: Tests that require running services (backend, etc.)

## Manual UI Testing

For manual UI testing, start both backend and frontend servers and follow the workflow:

1. Navigate to Settings page
2. Configure PDF generation preferences  
3. Test query functionality with different settings
4. Verify PDF generation behavior matches selections

## Running All Tests

```bash
# Run all Python tests
pytest tests/ -v

# Run only integration tests  
pytest tests/ -m integration -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html
```

## Adding New Tests

1. **Python Tests**: Add new `.py` files following pytest conventions
2. **Frontend Tests**: Add HTML files to `frontend/` directory
3. **Documentation**: Update relevant README files
4. **Markers**: Use appropriate pytest markers for test categorization
