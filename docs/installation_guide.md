# SocioRAG Installation & Setup Guide

## Quick Start

For a quick start experience, use the provided script:

```powershell
# From the project root
.\quick_start.ps1
```

This script will:
1. Start the backend server
2. Wait for the backend to be fully ready
3. Start the frontend development server
4. Open the application in your default web browser

You can then access:
- Frontend: http://localhost:5173
- Backend API: http://127.0.0.1:8000
- API Documentation: http://127.0.0.1:8000/docs

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Python**: 3.12.9 (required for compatibility)
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 2GB free space for dependencies and models
- **Internet**: Required for model downloads and API access

### Recommended Requirements
- **Memory**: 16GB RAM for optimal performance
- **Storage**: 10GB free space for large document processing
- **CPU**: Multi-core processor for concurrent processing
- **GPU**: Optional, for accelerated embeddings (future feature)

## Installation Methods

### Method 1: Conda Installation (Recommended)

Conda provides the most reliable environment management with system dependencies.

```bash
# 1. Install Miniconda (if not already installed)
# Download from: https://docs.conda.io/en/latest/miniconda.html

# 2. Clone the repository
git clone <repository-url>
cd sociorag

# 3. Create environment from environment.yml
conda env create -f environment.yml

# 4. Activate the environment
conda activate sociorag

# 5. Download required spaCy model
python -m spacy download en_core_web_sm

# 6. Install Playwright browsers for PDF generation
playwright install
```

### Method 2: pip Installation

Using pip with virtual environment for Python package management.

```bash
# 1. Clone the repository
git clone <repository-url>
cd sociorag

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows Command Prompt:
.\.venv\Scripts\activate.bat
# Unix/macOS:
source .venv/bin/activate

# 4. Upgrade pip
python -m pip install --upgrade pip

# 5. Install dependencies
pip install -r requirements.txt

# 6. Download spaCy model
python -m spacy download en_core_web_sm

# 7. Install PDF generation dependencies (optional)
# Note: Playwright requires browser installation
playwright install
```

### Method 3: Development Installation

For contributors and advanced users who want to modify the codebase.

```bash
# 1. Follow Method 1 or 2 for environment setup

# 2. Install in development mode
pip install -e .

# 3. Install development dependencies
pip install -r requirements-dev.txt

# 4. Install pre-commit hooks (optional)
pre-commit install

# 5. Run tests to verify installation
pytest tests/
```

## Configuration Setup

### 1. Environment Variables

Create a `.env` file from the example template:

```bash
# Copy the example file
cp .env.example .env

# Edit the .env file with your settings
nano .env  # or use your preferred editor
```

**Required Environment Variables:**
```env
# OpenRouter API configuration
OPENROUTER_API_KEY=your_api_key_here

# Database paths (use absolute paths)
GRAPH_DB_PATH=d:\sociorag\graph.db
VECTOR_STORE_PATH=d:\sociorag\vector_store

# Model configurations
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
ANSWER_LLM_MODEL=anthropic/claude-3-haiku

# Logging level
LOG_LEVEL=INFO
```

**Optional Environment Variables:**
```env
# Performance tuning
CHUNK_SIM_THRESHOLD=0.85
ENTITY_SIM_THRESHOLD=0.90
TOP_K_RESULTS=100
TOP_K_RERANK=15

# Resource limits
HISTORY_LIMIT=50
SAVED_LIMIT=50
MAX_CONTEXT_FRACTION=0.4

# PDF generation
PDF_THEME_PATH=d:\sociorag\resources\pdf_theme.css
```

### 2. Configuration File (Optional)

Create a `config.yaml` file for advanced configuration:

```yaml
# config.yaml
paths:
  base_dir: "d:/sociorag"
  input_dir: "d:/sociorag/input"
  saved_dir: "d:/sociorag/saved"
  vector_dir: "d:/sociorag/vector_store"
  graph_db: "d:/sociorag/graph.db"
  pdf_theme: "d:/sociorag/resources/pdf_theme.css"

models:
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
  reranker_model: "sentence-transformers/ms-marco-MiniLM-L-2-v2"
  entity_llm_model: "anthropic/claude-3-haiku"
  answer_llm_model: "anthropic/claude-3-haiku"
  translate_llm_model: "anthropic/claude-3-haiku"

thresholds:
  chunk_sim: 0.85
  entity_sim: 0.90
  graph_sim: 0.50
  top_k: 100
  top_k_rerank: 15
  max_context_fraction: 0.4

resources:
  spacy_model: "en_core_web_sm"
  log_level: "INFO"

limits:
  history_limit: 50
  saved_limit: 50
```

### 3. API Key Setup

#### OpenRouter API Key
1. Visit [OpenRouter](https://openrouter.ai/)
2. Create an account and generate an API key
3. Add the key to your `.env` file:
   ```env
   OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
   ```

#### Alternative LLM Providers
If using other providers, update the configuration accordingly:

```env
# For OpenAI
OPENAI_API_KEY=your_openai_key
ANSWER_LLM_MODEL=gpt-3.5-turbo

# For Anthropic
ANTHROPIC_API_KEY=your_anthropic_key
ANSWER_LLM_MODEL=claude-3-haiku
```

## Database Initialization

### 1. Create Required Directories

```bash
# Create necessary directories
mkdir -p input saved vector_store docs

# Set permissions (Unix/macOS only)
chmod 755 input saved vector_store docs
```

### 2. Initialize Databases

The databases will be created automatically on first run, but you can initialize them manually:

```python
# Run the initialization script
python scripts/init_databases.py

# Or initialize through the API
python -c "
from backend.app.core.singletons import DatabaseSingleton
db = DatabaseSingleton().get()
print('Database initialized successfully')
"
```

## Model Downloads

### 1. spaCy Models

```bash
# Download the English language model
python -m spacy download en_core_web_sm

# Verify the download
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('spaCy model loaded successfully')"
```

### 2. Embedding Models

Models will be downloaded automatically on first use, but you can pre-download them:

```python
# Pre-download embedding models
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print('Embedding model downloaded successfully')
"
```

## Verification

### 1. Basic Installation Test

```bash
# Run the basic test
python test_phase5_simple.py
```

Expected output:
```
✅ Configuration loaded successfully
✅ Logger initialized
✅ LLM client created
✅ Answer generated successfully
✅ History recorded
✅ PDF generated successfully
All tests passed! 🎉
```

### 2. Comprehensive Test Suite

```bash
# Run the full test suite
python test_phase5.py
```

This will test:
- Configuration management
- Database connections
- LLM integration
- Answer generation
- PDF export
- History tracking

### 3. API Server Test

```bash
# Start the API server
python -m backend.app.main

# In another terminal, test the endpoints
curl http://localhost:8000/api/qa/stats
```

Expected response:
```json
{
  "total_queries": 0,
  "avg_response_time": 0,
  "total_sources_used": 0,
  "queries_today": 0,
  "most_common_topics": []
}
```

## Troubleshooting

### Common Installation Issues

#### 1. WeasyPrint Installation Fails

**Problem**: WeasyPrint requires system dependencies
**Solution**:
```bash
# Ubuntu/Debian
sudo apt-get install python3-dev python3-pip python3-cffi python3-brotli libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0

# macOS
brew install pango

# Windows (use conda)
conda install -c conda-forge weasyprint
```

#### 2. spaCy Model Download Fails

**Problem**: Network issues or permission errors
**Solution**:
```bash
# Try direct download
python -m spacy download en_core_web_sm --user

# Or download manually
wget https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl
pip install en_core_web_sm-3.7.1-py3-none-any.whl
```

#### 3. SQLite-vec Not Found

**Problem**: Vector database extension not available
**Solution**:
```bash
# Install from conda-forge
conda install -c conda-forge sqlite-vec

# Or compile from source
git clone https://github.com/asg017/sqlite-vec.git
cd sqlite-vec
make loadable
```

#### 4. Permission Errors on Windows

**Problem**: PowerShell execution policy restrictions
**Solution**:
```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate the virtual environment
.\.venv\Scripts\Activate.ps1
```

#### 5. Memory Issues

**Problem**: Out of memory during model loading
**Solution**:
```bash
# Reduce model sizes in config
export MAX_CONTEXT_FRACTION=0.2
export TOP_K=50
export TOP_K_RERANK=5

# Or increase virtual memory
# Windows: Increase paging file size
# Linux: Increase swap space
```

### Performance Optimization

#### 1. CPU Optimization

```bash
# Set environment variables for better CPU usage
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
export NUMEXPR_MAX_THREADS=4
```

#### 2. Memory Optimization

```python
# In config.yaml
limits:
  max_context_fraction: 0.3  # Reduce context size
  top_k: 50                  # Reduce result count
  top_k_rerank: 10          # Reduce reranking candidates
```

#### 3. Disk Space Management

```bash
# Clean up downloaded models and caches
python -c "
import shutil
import os
if os.path.exists('.cache'):
    shutil.rmtree('.cache')
print('Cache cleaned')
"
```

## Development Setup

### IDE Configuration

#### VS Code
Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"]
}
```

#### PyCharm
1. Open the project directory
2. Configure Python interpreter to use the virtual environment
3. Set source root to the project directory
4. Configure test runner to use pytest

### Code Quality Tools

```bash
# Install development dependencies
pip install black isort flake8 mypy pytest

# Format code
black .
isort .

# Check code quality
flake8 .
mypy backend/

# Run tests
pytest tests/
```

## Production Deployment

### Docker Setup (Future)

```dockerfile
# Dockerfile (example for future implementation)
FROM python:3.12.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment-Specific Configuration

```bash
# Development
export ENV=development
export LOG_LEVEL=DEBUG

# Production
export ENV=production
export LOG_LEVEL=WARNING
```

## Support

### Getting Help

1. **Documentation**: Check the `docs/` directory for comprehensive guides
2. **Issues**: Search existing issues in the repository
3. **Community**: Join the project discussions
4. **Contact**: Reach out to the development team

### Reporting Issues

When reporting issues, include:
- Operating system and version
- Python version
- Installation method used
- Complete error messages
- Steps to reproduce
- Expected vs. actual behavior

### Contributing

See the contribution guidelines for:
- Code style requirements
- Testing procedures
- Pull request process
- Development workflow

This installation guide should get you up and running with SocioRAG quickly and reliably. Follow the troubleshooting section if you encounter any issues during setup.
