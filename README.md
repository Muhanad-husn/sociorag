# SocioGraph

A system for analyzing and visualizing social dynamics in texts.

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
   ```   ### Using pip

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

3. **Repository Structure**   ```text
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

## Improved Entity Extraction

SocioGraph includes a robust entity extraction system that uses LLMs to extract entities and relationships from text:

- **Resilient JSON Parsing**: Handles various response formats from the OpenRouter API
- **Multiple Fallback Strategies**: Ensures maximum data extraction even from malformed responses
- **Entity Validation**: Guarantees that extracted entities conform to the required schema
- **Detailed Documentation**: See [Entity Extraction Improvements](./docs/entity_extraction_improvements.md)

To test the entity extraction:

```powershell
# Run the entity extraction module test
python test_entity_extraction_module.py
```

For more details, see [Entity Extraction Documentation](./docs/entity_extraction_complete.md).

## Enhanced Entity Extraction

Building on the improved entity extraction, SocioGraph now offers an enhanced version with advanced features:

- **Retry Mechanism**: Automatically retries failed API calls for higher reliability
- **Response Caching**: Avoids redundant API calls for significant performance gains
- **Batch Processing**: Processes multiple chunks concurrently with controlled concurrency
- **Structured Error Reporting**: Provides detailed debug information for better troubleshooting
- **Advanced JSON Parsing**: Adds additional parsing strategies for complex malformed responses

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

## License

TBD
