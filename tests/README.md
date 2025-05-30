# SocioRAG Testing Framework

This directory contains comprehensive tests for various SocioRAG functionalities.

## Test Categories

### PDF Generation Tests
Tests for the PDF generation user choice functionality.

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
