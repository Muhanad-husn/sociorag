# SocioRAG Testing Framework

This directory contains comprehensive tests for various SocioRAG functionalities.

## Test Categories

### PDF Generation Tests
Tests for the PDF generation user choice functionality.

### Frontend Tests
Browser-based tests for frontend functionality (see `frontend/` directory).

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
- `SOCIORAG_API_URL`: Backend API URL (default: http://127.0.0.1:8000)
- `SOCIORAG_FRONTEND_URL`: Frontend URL (default: http://localhost:5173)

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

## Test Markers

- `@pytest.mark.integration`: Tests that require running services (backend, etc.)

## Manual UI Testing

For manual UI testing, start both backend and frontend servers and follow the workflow:

1. Navigate to Settings page
2. Toggle PDF generation setting
3. Ask questions and verify PDF download behavior
4. Test with both English and Arabic content
5. Verify RTL layout works correctly

See `docs/pdf_generation_user_choice_completion_report.md` for detailed testing instructions.
