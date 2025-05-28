# SocioRAG Developer Guide

## Development Environment Setup

### Prerequisites

Before contributing to SocioGraph, ensure you have the following installed:

- **Python 3.12.9** (exact version required for compatibility)
- **Git 2.30+** for version control
- **VS Code** or **PyCharm** (recommended IDEs)
- **Miniconda** or **Anaconda** (recommended package management)

### Setting Up Development Environment

#### 1. Clone and Setup Repository

```bash
# Clone the repository
git clone <repository-url>
cd sociorag

# Create development environment
conda env create -f environment.yml
conda activate sociorag

# Or using pip
python -m venv .venv
source .venv/bin/activate  # Unix/macOS
.\.venv\Scripts\Activate.ps1  # Windows PowerShell

# Install development dependencies
pip install -r requirements-dev.txt
```

#### 2. IDE Configuration

**VS Code Setup** (`.vscode/settings.json`):
```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

**PyCharm Setup**:
1. Open project directory
2. Configure Python interpreter to use virtual environment
3. Enable pytest as test runner
4. Configure code style to use Black formatter

#### 3. Pre-commit Hooks

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## Project Structure Deep Dive

### Directory Organization

```
sociorag/
├── backend/                 # Backend application code
│   └── app/
│       ├── core/           # Core infrastructure and singletons
│       ├── api/            # FastAPI endpoints and routers
│       ├── answer/         # Answer generation pipeline
│       ├── retriever/      # Document retrieval and search
│       ├── ingest/         # Data ingestion and processing
│       └── main.py         # Application entry point
├── ui/                     # Frontend code (future development)
├── tests/                  # Test suites and test data
├── docs/                   # Documentation files
├── scripts/                # Utility and maintenance scripts
├── resources/              # Static resources (CSS, templates)
├── input/                  # Input documents directory
├── saved/                  # Generated outputs and exports
├── vector_store/           # Vector database files
├── instructions/           # Prompt templates and instructions
├── requirements.txt        # Python dependencies
├── environment.yml         # Conda environment specification
├── config.yaml.example    # Configuration template
└── .env.example           # Environment variables template
```

### Code Organization Principles

1. **Modularity**: Each module has a single responsibility
2. **Dependency Injection**: Use singletons for shared resources
3. **Type Hints**: All functions and methods must have type annotations
4. **Error Handling**: Comprehensive exception handling with logging
5. **Documentation**: Docstrings for all public functions and classes

## Coding Standards

### Python Style Guide

We follow PEP 8 with specific modifications:

```python
# Example of proper code style
from typing import List, Dict, Optional, AsyncGenerator
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class QueryResult:
    """Represents a query result with metadata."""
    answer: str
    sources: List[Dict[str, str]]
    response_time: float
    confidence: Optional[float] = None

async def generate_answer(
    question: str,
    context: List[str],
    include_citations: bool = True
) -> AsyncGenerator[str, None]:
    """Generate streaming answer for given question and context.
    
    Args:
        question: User's question
        context: Retrieved context chunks
        include_citations: Whether to include source citations
        
    Yields:
        Answer tokens as they are generated
        
    Raises:
        ValueError: If question is empty
        LLMError: If LLM generation fails
    """
    if not question.strip():
        raise ValueError("Question cannot be empty")
    
    try:
        # Implementation here
        pass
    except Exception as e:
        logger.error(f"Answer generation failed: {e}")
        raise
```

### Code Quality Tools

#### 1. Black Formatter
```bash
# Format all Python files
black .

# Check without formatting
black --check .
```

#### 2. isort for Import Sorting
```bash
# Sort imports
isort .

# Configuration in pyproject.toml
[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
```

#### 3. Flake8 for Linting
```bash
# Run linting
flake8 .

# Configuration in setup.cfg
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,.venv
```

#### 4. MyPy for Type Checking
```bash
# Run type checking
mypy backend/

# Configuration in mypy.ini
[mypy]
python_version = 3.12
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

## Testing Strategy

The project uses a simplified testing approach focusing on pipeline tests rather than comprehensive end-to-end tests. This makes the codebase more maintainable and focuses on testing core functionality.

### Test Structure

```
tests/
├── retriever/             # Tests for the retrieval system
│   ├── test_embedding.py  # Tests for embedding functionality
│   ├── test_similarity_functions.py  # Tests for similarity functions
│   └── test_sqlite_vec_utils.py  # Tests for SQLite vector utilities
├── test_enhanced_entity_extraction.py  # Tests for enhanced entity extraction
├── test_entity_extraction_module.py    # Tests for entity extraction module
└── __init__.py            # Test package initialization
```

### Writing Tests

#### Unit Test Example
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.app.answer.generator import AnswerGenerator

@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    client = AsyncMock()
    client.create_chat.return_value = AsyncMock()
    return client

@pytest.fixture
def answer_generator(mock_llm_client):
    """Answer generator with mocked dependencies."""
    return AnswerGenerator(llm_client=mock_llm_client)

@pytest.mark.asyncio
async def test_generate_answer_success(answer_generator, mock_llm_client):
    """Test successful answer generation."""
    # Arrange
    question = "What is the main theme?"
    context = ["Sample context text"]
    
    mock_response = AsyncMock()
    mock_response.__aiter__.return_value = ["Test", " answer"]
    mock_llm_client.create_chat.return_value = mock_response
    
    # Act
    result = []
    async for token in answer_generator.generate_answer(question, context):
        result.append(token)
    
    # Assert
    assert "".join(result) == "Test answer"
    mock_llm_client.create_chat.assert_called_once()

@pytest.mark.asyncio
async def test_generate_answer_empty_question(answer_generator):
    """Test error handling for empty question."""
    with pytest.raises(ValueError, match="Question cannot be empty"):
        async for _ in answer_generator.generate_answer("", []):
            pass
```

#### Integration Test Example
```python
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture
def client():
    """Test client for API testing."""
    return TestClient(app)

def test_qa_ask_endpoint(client):
    """Test Q&A ask endpoint."""
    response = client.post(
        "/api/qa/ask",
        json={"question": "Test question", "include_citations": True}
    )
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]

def test_qa_history_endpoint(client):
    """Test Q&A history endpoint."""
    response = client.get("/api/qa/history")
    assert response.status_code == 200
    data = response.json()
    assert "history" in data
    assert "total_count" in data
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_answer/test_generator.py

# Run with coverage
pytest --cov=backend --cov-report=html

# Run only fast tests (skip slow integration tests)
pytest -m "not slow"

# Run tests in parallel
pytest -n auto
```

## Database Development

### Schema Management

#### Vector Store Schema
```sql
-- Create vector store tables
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY,
    document_id TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata TEXT, -- JSON metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE embeddings (
    chunk_id INTEGER PRIMARY KEY,
    embedding BLOB, -- Vector embedding
    FOREIGN KEY (chunk_id) REFERENCES chunks(id)
);
```

#### Graph Database Schema
```sql
-- Create entity tables
CREATE TABLE entities (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE relationships (
    id INTEGER PRIMARY KEY,
    entity1_id INTEGER,
    entity2_id INTEGER,
    relationship_type TEXT,
    confidence REAL,
    source_document TEXT,
    FOREIGN KEY (entity1_id) REFERENCES entities(id),
    FOREIGN KEY (entity2_id) REFERENCES entities(id)
);
```

### Database Migration Scripts

```python
# scripts/migrate_database.py
import sqlite3
from pathlib import Path

def migrate_vector_store(db_path: Path):
    """Migrate vector store to latest schema."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check current schema version
    cursor.execute("PRAGMA user_version")
    version = cursor.fetchone()[0]
    
    if version < 1:
        # Apply migration 1
        cursor.execute("""
            ALTER TABLE chunks 
            ADD COLUMN metadata TEXT
        """)
        cursor.execute("PRAGMA user_version = 1")
    
    conn.commit()
    conn.close()
```

## API Development

### Adding New Endpoints

#### 1. Define Router
```python
# backend/app/api/new_feature.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/api/new-feature", tags=["new-feature"])

class FeatureRequest(BaseModel):
    parameter: str
    options: List[str] = []

class FeatureResponse(BaseModel):
    result: str
    status: str

@router.post("/process", response_model=FeatureResponse)
async def process_feature(request: FeatureRequest):
    """Process new feature request."""
    try:
        # Implementation
        return FeatureResponse(result="success", status="completed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### 2. Register Router
```python
# backend/app/main.py
from backend.app.api.new_feature import router as new_feature_router

app.include_router(new_feature_router)
```

#### 3. Add Tests
```python
# tests/integration/test_api/test_new_feature.py
def test_process_feature_success(client):
    """Test successful feature processing."""
    response = client.post(
        "/api/new-feature/process",
        json={"parameter": "test", "options": ["option1"]}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
```

### Error Handling Standards

```python
from fastapi import HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class SocioRAGException(Exception):
    """Base exception for SocioRAG application."""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)

class LLMError(SocioRAGException):
    """LLM-related errors."""
    pass

class RetrievalError(SocioRAGException):
    """Document retrieval errors."""
    pass

def handle_api_error(e: Exception) -> HTTPException:
    """Convert application exceptions to HTTP exceptions."""
    if isinstance(e, SocioRAGException):
        logger.error(f"Application error: {e.message}", extra=e.details)
        return HTTPException(status_code=400, detail=e.message)
    else:
        logger.error(f"Unexpected error: {str(e)}")
        return HTTPException(status_code=500, detail="Internal server error")
```

## Module Development

### Creating New Modules

#### 1. Module Structure
```python
# backend/app/new_module/__init__.py
"""New module for specific functionality."""

from .main_component import MainComponent
from .helper import HelperClass

__all__ = ["MainComponent", "HelperClass"]
```

#### 2. Main Component
```python
# backend/app/new_module/main_component.py
from typing import List, Optional
from backend.app.core.singletons import LoggerSingleton
import logging

logger = LoggerSingleton().get()

class MainComponent:
    """Main component for new module functionality."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        logger.info("MainComponent initialized")
    
    async def process(self, data: List[str]) -> List[str]:
        """Process data with new module logic."""
        try:
            # Implementation
            results = []
            for item in data:
                processed = self._process_item(item)
                results.append(processed)
            return results
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            raise
    
    def _process_item(self, item: str) -> str:
        """Process individual item."""
        # Implementation
        return item.upper()
```

#### 3. Integration with Core
```python
# backend/app/core/singletons.py
from backend.app.new_module import MainComponent

class NewModuleSingleton:
    """Singleton for new module component."""
    _instance = None
    _component = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get(self) -> MainComponent:
        """Get or create main component instance."""
        if self._component is None:
            config = ConfigSingleton().get()
            self._component = MainComponent(config.dict())
        return self._component
```

## Performance Optimization

### Profiling and Benchmarking

#### 1. Performance Testing
```python
# tests/performance/test_answer_generation.py
import time
import pytest
from backend.app.answer.generator import AnswerGenerator

@pytest.mark.slow
@pytest.mark.asyncio
async def test_answer_generation_performance():
    """Test answer generation performance."""
    generator = AnswerGenerator()
    question = "What are the main themes in the documents?"
    context = ["Sample context"] * 10
    
    start_time = time.time()
    
    result = []
    async for token in generator.generate_answer(question, context):
        result.append(token)
    
    elapsed_time = time.time() - start_time
    
    assert elapsed_time < 5.0  # Should complete within 5 seconds
    assert len("".join(result)) > 0
```

#### 2. Memory Profiling
```python
# scripts/profile_memory.py
import tracemalloc
from backend.app.answer.generator import AnswerGenerator

def profile_answer_generation():
    """Profile memory usage of answer generation."""
    tracemalloc.start()
    
    # Run operation
    generator = AnswerGenerator()
    # ... perform operations
    
    current, peak = tracemalloc.get_traced_memory()
    print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
    print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
    
    tracemalloc.stop()
```

### Optimization Strategies

#### 1. Caching Implementation
```python
from functools import lru_cache
from typing import List, Tuple

class CachedRetriever:
    """Retriever with caching for improved performance."""
    
    @lru_cache(maxsize=1000)
    def _get_cached_embeddings(self, text: str) -> Tuple[float, ...]:
        """Get cached embeddings for text."""
        # Implementation
        pass
    
    async def retrieve_with_cache(self, query: str) -> List[str]:
        """Retrieve context with caching."""
        embeddings = self._get_cached_embeddings(query)
        # Use cached embeddings for retrieval
        pass
```

#### 2. Async Optimization
```python
import asyncio
from typing import List

async def batch_process_documents(documents: List[str]) -> List[dict]:
    """Process documents concurrently for better performance."""
    semaphore = asyncio.Semaphore(5)  # Limit concurrency
    
    async def process_single(doc: str) -> dict:
        async with semaphore:
            # Process single document
            await asyncio.sleep(0.1)  # Simulate processing
            return {"doc": doc, "processed": True}
    
    tasks = [process_single(doc) for doc in documents]
    results = await asyncio.gather(*tasks)
    return results
```

## Debugging and Troubleshooting

### Logging Best Practices

```python
import logging
from backend.app.core.singletons import LoggerSingleton

logger = LoggerSingleton().get()

def complex_operation(data: dict) -> dict:
    """Example of proper logging in operations."""
    operation_id = data.get("id", "unknown")
    
    logger.info(f"Starting operation {operation_id}")
    logger.debug(f"Input data: {data}")
    
    try:
        # Process data
        result = {"processed": True, "id": operation_id}
        
        logger.info(
            f"Operation {operation_id} completed successfully",
            extra={"operation_id": operation_id, "result_size": len(result)}
        )
        return result
        
    except Exception as e:
        logger.error(
            f"Operation {operation_id} failed: {str(e)}",
            extra={"operation_id": operation_id, "error_type": type(e).__name__},
            exc_info=True
        )
        raise
```

### Common Debug Scenarios

#### 1. Database Connection Issues
```python
# scripts/debug_database.py
import sqlite3
from pathlib import Path

def debug_database_connection():
    """Debug database connectivity issues."""
    try:
        db_path = Path("graph.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test basic operations
        cursor.execute("SELECT COUNT(*) FROM entities")
        count = cursor.fetchone()[0]
        print(f"Entities count: {count}")
        
        conn.close()
        print("Database connection successful")
        
    except Exception as e:
        print(f"Database connection failed: {e}")
```

#### 2. LLM Integration Issues
```python
# scripts/debug_llm.py
from backend.app.core.singletons import LLMClientSingleton

async def debug_llm_connection():
    """Debug LLM client connectivity."""
    try:
        llm_client = LLMClientSingleton().get()
        
        # Test simple request
        response = await llm_client.create_chat(
            messages=[{"role": "user", "content": "Hello"}],
            model="anthropic/claude-3-haiku"
        )
        
        print("LLM connection successful")
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"LLM connection failed: {e}")
```

## Contributing Guidelines

### Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-feature-name
   ```

2. **Make Changes**
   - Follow coding standards
   - Add comprehensive tests
   - Update documentation

3. **Pre-commit Checks**
   ```bash
   # Run all quality checks
   black .
   isort .
   flake8 .
   mypy backend/
   pytest
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

5. **Create Pull Request**
   - Include clear description
   - Reference related issues
   - Add screenshots if applicable

### Code Review Checklist

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] New functionality has comprehensive tests
- [ ] Documentation is updated
- [ ] No sensitive information in code
- [ ] Performance impact considered
- [ ] Error handling is comprehensive
- [ ] Logging is appropriate

### Release Process

1. **Version Bump**
   ```bash
   # Update version in pyproject.toml
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **Release Notes**
   - Document new features
   - List breaking changes
   - Include migration instructions

3. **Deployment**
   - Update production environment
   - Run migration scripts
   - Monitor for issues

This developer guide provides comprehensive information for contributing to SocioRAG effectively. Follow these guidelines to maintain code quality and consistency across the project.
