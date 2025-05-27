# SocioGraph

A system for analyzing and visualizing social dynamics in texts.

## Project Status

**All Major Development Phases Complete**: The core backend, API, and frontend application (Preact + Tailwind) are complete. The project is currently in Phase 8: Testing & Utilities. For more details, see the [Project Overview](./docs/project_overview.md) and the main [Rebuild Plan](./instructions/sociograph_rebuild_plan.md).

## Setup Instructions

1. **Prerequisites**
   - Python 3.12.9
   - [Miniconda](https://docs.conda.io/en/latest/miniconda.html) ≥ 23.10 (recommended)
   - Git 2.30+

2. **Environment Setup**

   Choose one of the following methods:

   ### Using Conda (Recommended)

   ```bash
   # Clone the repository
   git clone <repository-url>
   cd sociograph

   # Create environment from environment.yml
   conda env create -f environment.yml
   conda activate sociograph
   ```

   ### Using pip

   ```bash
   # Clone the repository
   git clone <repository-url>
   cd sociograph

   # Create and activate virtual environment
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1  # On Windows
   source .venv/bin/activate     # On Unix/macOS

   # Install dependencies
   python -m pip install --upgrade pip
   pip install -r requirements.txt

   # Download spaCy model (required for both pip and conda installations)
   python -m spacy download en_core_web_sm
   ```

   Note: The `requirements.txt` file contains only the direct dependencies. Using conda with `environment.yml` is recommended as it provides a more complete and tested environment.

3. **Repository Structure**

   ```text
   backend/              # Backend service
     app/
       core/            # Core business logic
       ingest/         # Data ingestion
         entity_extraction.py  # Robust entity extraction
         pipeline_fixed_improved.py  # Improved ingestion pipeline
       retriever/      # Vector store and retrieval
       api/           # FastAPI endpoints
     tests/           # Backend tests
   ui/src/            # Frontend code
   resources/         # Static resources
   input/            # Input data files
   saved/            # Saved models and states
   vector_store/     # Vector embeddings storage
   docs/             # Documentation
     entity_extraction_improvements.md  # Entity extraction documentation
   ```

4. **Development**

   - The project uses Python 3.12.9
   - Main dependencies include FastAPI, LangChain, ChromaDB, and spaCy
   - Vector storage using sqlite-vec for efficient similarity search
   - Frontend development path to be determined in later phases

## Global Configuration

The project uses a centralized configuration system that allows for easy adjustment of parameters:

### Changing Defaults

1. Copy `.env.example` → `.env` and tweak numeric thresholds.
2. Or create `config.yaml` and pass its path to `get_config()`:

```python
from backend.app.core.config import get_config
cfg = get_config("config.yaml")
print(cfg.TOP_K)   # 50
```

All configuration parameters are defined in `backend/app/core/config.py` and include:

- **Paths**: BASE_DIR, INPUT_DIR, SAVED_DIR, VECTOR_DIR, GRAPH_DB, PDF_THEME
- **Models**: EMBEDDING_MODEL, RERANKER_MODEL, ENTITY_LLM_MODEL, ANSWER_LLM_MODEL, TRANSLATE_LLM_MODEL
- **Thresholds/Parameters**: CHUNK_SIM (0.85), ENTITY_SIM (0.90), GRAPH_SIM (0.95), TOP_K (100), TOP_K_RERANK (15), MAX_CONTEXT_FRACTION (0.4)
- **Resources**: SPACY_MODEL, LOG_LEVEL
- **Limits**: HISTORY_LIMIT (15), SAVED_LIMIT (15)

## Enhanced Entity Extraction

SocioGraph includes a robust entity extraction system that uses LLMs to extract entities and relationships from text. Key features include:

- **Resilient JSON Parsing**: Handles various response formats from the OpenRouter API.
- **Multiple Fallback Strategies**: Ensures maximum data extraction even from malformed responses.
- **Entity Validation**: Guarantees that extracted entities conform to the required schema.
- **Retry Mechanism**: Automatically retries failed API calls for higher reliability.
- **Response Caching**: Avoids redundant API calls for significant performance gains.
- **Batch Processing**: Processes multiple chunks concurrently with controlled concurrency.
- **Structured Error Reporting**: Provides detailed debug information for better troubleshooting.
- **Advanced JSON Parsing**: Adds additional parsing strategies for complex malformed responses.

To use the enhanced entity extraction:

```python
from backend.app.ingest.enhanced_entity_extraction import (
    extract_entities_from_text,
    extract_entities_with_retry,
    batch_process_chunks,
    clear_cache
)

# Simple extraction
entities = await extract_entities_from_text(chunk)

# Extraction with retry and debug info
entities, debug_info = await extract_entities_with_retry(chunk, max_retries=3)

# Batch processing
batch_results = await batch_process_chunks(chunks, batch_size=5, concurrency_limit=3)
```

To test and benchmark the enhanced functionality:

```powershell
# Test the enhanced entity extraction
python tests/test_enhanced_entity_extraction.py

# See a simple example of enhanced entity extraction
python tests/example_enhanced_entity_extraction.py
```

For detailed documentation, see:

- [Enhanced Entity Extraction](./docs/enhanced_entity_extraction.md)
- [Complete Entity Extraction Documentation](./docs/entity_extraction_complete.md)
- [Cleanup Summary](./docs/entity_extraction_cleanup_summary.md)

## Project Organization

- `backend/app/ingest/` - Core implementation files
- `tests/` - Test and example files
- `scripts/` - Utility scripts
- `docs/` - Documentation files

## Comprehensive Documentation

The project includes extensive documentation to help users and developers:

### User Documentation

- **[Installation Guide](./docs/installation_guide.md)** - Complete setup instructions for all platforms
- **[API Documentation](./docs/api_documentation.md)** - Comprehensive API reference with examples
- **[API Endpoints Reference](./docs/api_endpoints_reference.md)** - Quick reference for all available endpoints
- **[Project Overview](./docs/project_overview.md)** - High-level project summary and current status

### Developer Documentation

- **[Architecture Documentation](./docs/architecture_documentation.md)** - System design and component overview
- **[Developer Guide](./docs/developer_guide.md)** - Development environment, coding standards, and contribution guidelines
- **[Phase 6 Implementation Summary](./docs/phase6_implementation_summary.md)** - FastAPI backend completion details
- **[Phase 6 Implementation Plan](./docs/phase6_implementation_plan.md)** - Roadmap for FastAPI backend implementation

### Technical Documentation

- **[Enhanced Entity Extraction](./docs/enhanced_entity_extraction.md)** - Advanced entity extraction capabilities
- **[Phase 6 Implementation Summary](./docs/phase6_implementation_summary.md)** - API integration and WebSocket support
- **[Phase 5 Implementation Summary](./docs/phase5_implementation_summary.md)** - Answer generation and PDF export details
- **Additional Phase Documentation** - Complete implementation reports for all phases

## Quick Start

1. **Setup Environment**
   ```bash
   conda env create -f environment.yml
   conda activate sociograph
   python -m spacy download en_core_web_sm
   ```

2. **Configure API Keys**

   ```bash
   cp .env.example .env
   # Edit .env with your OpenRouter API key
   ```

3. **Test Installation**

   ```bash
   python test_phase5_simple.py
   ```

4. **Start API Server**

   ```bash
   python -m backend.app.main
   # Server will be available at http://127.0.0.1:8000
   # API docs available at http://127.0.0.1:8000/docs
   ```

5. **Using the API**

   **Document Management:**

   ```bash
   # Reset corpus (clear existing data)
   curl -X POST http://127.0.0.1:8000/api/ingest/reset

   # Upload a PDF document
   curl -X POST -F "file=@./sample.pdf" http://127.0.0.1:8000/api/ingest/upload

   # Manually trigger processing
   curl -X POST http://127.0.0.1:8000/api/ingest/process

   # Stream processing progress (SSE)
   curl http://127.0.0.1:8000/api/ingest/progress
   ```

   **Question Answering:**

   ```bash
   # Ask a question (streaming response)
   curl http://127.0.0.1:8000/api/qa/ask -H "Content-Type: application/json" \
     -d '{"question": "What are the main themes in the document?"}'

   # Get query history
   curl http://127.0.0.1:8000/api/history/

   # Get usage statistics
   curl http://127.0.0.1:8000/api/history/stats
   ```

6. **Testing All Endpoints**

   ```bash
   # Test all API endpoints
   python scripts/test_phase6_api.py all

   # Test specific endpoint (e.g., WebSocket)
   python scripts/test_phase6_api.py websocket
   ```

## Current Features (Phase 6 Complete)

- ✅ **Enhanced Entity Extraction** - LLM-powered entity and relationship extraction
- ✅ **Vector Storage & Retrieval** - SQLite-vec based semantic search
- ✅ **Streaming Q&A System** - Real-time answer generation with citations
- ✅ **PDF Export** - Professional report generation with WeasyPrint
- ✅ **Query History** - Analytics and tracking with JSONL logging
- ✅ **FastAPI Integration** - Complete REST API with comprehensive endpoints
- ✅ **Server-Sent Events** - Real-time streaming for progress and answers
- ✅ **WebSocket Support** - Bidirectional communication with heartbeat mechanisms
- ✅ **Ingestion API** - Document upload, processing, and monitoring endpoints
- ✅ **History Management** - Full history tracking and retrieval with filtering
- ✅ **API Documentation** - Interactive Swagger UI with endpoint reference

## Next Steps

With the successful completion of Phase 7 (Frontend Development), the project is now ready to move on to:

### Phase 8: Testing & Utilities

- **Unit tests** (`pytest`) for singletons, ingest, retrieval.
- **Fixture PDF** in `tests/fixtures/`.
- CLI helpers: `python -m sociograph.reset`, `python -m sociograph.ingest input/*.pdf`.
- Optional GitHub Actions CI (runs tests).

See the [Phase 8 Deep Dive Plan](./instructions/phase8_deep_dive_plan.md) for detailed roadmap.

## Support and Contributing

- **Issues**: Report bugs and request features through the issue tracker
- **Contributing**: See [Developer Guide](./docs/developer_guide.md) for contribution guidelines
- **Documentation**: All documentation is in the `docs/` directory

## License

TBD
