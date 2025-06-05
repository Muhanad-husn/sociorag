# SocioRAG Installation Guide

## 🚀 Quick Start (< 2 minutes)

### ⚡ Instant Setup (Recommended)
```powershell
# Clone and setup environment
git clone https://github.com/your-username/sociorag.git
cd sociorag
cp .env.example .env
cp config.yaml.example config.yaml

# Start application - auto-installs all dependencies!
.\start_production.ps1
```

**That's it!** The startup script automatically:
- ✅ Detects and installs missing dependencies
- ✅ Handles npm, pnpm, or yarn (auto-detected)
- ✅ Properly manages Windows paths with spaces
- ✅ Starts both backend and frontend services
- ✅ Opens the application in your browser

### 🔧 Complete Setup (First-time)
```powershell
# For comprehensive setup including database initialization
.\setup.ps1

# Then start normally
.\start_production.ps1
```

### 📋 Manual Setup (Advanced Users)
```powershell
# 1. Create virtual environment (optional)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies manually
pip install -r requirements.txt
cd ui && npm install && cd ..

# 3. Set up environment
echo "OPENROUTER_API_KEY=your_key_here" > .env

# 4. Start services manually
python -m backend.app.main  # Terminal 1
cd ui && npm run dev        # Terminal 2
```

**Access Points:**

- **Frontend**: `http://localhost:5173`
- **Backend API**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs`
- **Admin Panel**: `http://localhost:8000/api/admin/status` 
- Frontend: http://localhost:5173 
- Backend: http://127.0.0.1:8000 
- API Docs: http://127.0.0.1:8000/docs

---

## 🛡️ System Requirements

- **Python**: 3.8+ (with pip)
- **Node.js**: 18+ (with npm) - automatically detected
- **Operating System**: Windows (PowerShell), Linux/macOS (with minor modifications)
- **Memory**: 4GB+ RAM recommended
- **Storage**: 2GB+ free space

## 🔄 Auto-Install Features

The startup scripts include intelligent dependency management:

### Frontend Dependencies
- **Auto-detection**: Checks for missing `node_modules` directory
- **Package Manager Support**: Automatically detects and uses npm, pnpm, or yarn
- **Windows Compatibility**: Handles paths with spaces (e.g., "Program Files")
- **Error Handling**: Clear error messages and automatic fallbacks

### Backend Dependencies
- **Python Environment**: Automatically detects Python installation
- **Dependency Validation**: Checks for required packages
- **Virtual Environment**: Works with or without virtual environments

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

### Production Deployment

For production deployment, see the [Production Deployment Guide](production_deployment_guide.md) for comprehensive instructions on setting up the application in a production environment.

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



---

# Configuration Guide

# SocioRAG Configuration Guide

## Overview

SocioGraph provides flexible configuration management through multiple methods, including a new web-based interface for API key management. This guide covers all configuration options and setup methods.

## Configuration Methods

### 1. Web Interface (Recommended) ⭐ NEW

The easiest way to configure SocioGraph is through the web interface:

1. **Start the Application**
   ```bash
   python -m backend.app.main
   ```

2. **Open Settings Page**
   - Navigate to `http://127.0.0.1:8000/settings` in your browser
   - Or click the "Settings" link in the navigation menu

3. **Configure API Keys**
   - Find the "System Configuration" section
   - Click "Configure/Update" next to "OpenRouter API Key"
   - Enter your API key in the secure password field
   - Click "Save Key"

**Features:**
- ✅ Real-time configuration status indicators
- ✅ Secure password input for API keys
- ✅ Automatic persistence to `.env` file
- ✅ No server restart required
- ✅ Immediate configuration reload
- ✅ Visual feedback with success/error messages

### 2. Environment File (.env)

**Traditional Method:**

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your preferred editor:
   ```properties
   # OpenRouter API Configuration
   OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
   
   # System Configuration
   LOG_LEVEL=INFO
   CHUNK_SIM=0.85
   
   # Performance Tuning
   TOP_K=100
   TOP_K_RERANK=15
   MAX_CONTEXT_FRACTION=0.4
   ```

3. Restart the application to apply changes

### 3. YAML Configuration File

**Advanced Users:**

1. Create a `config.yaml` file:
   ```yaml
   # Model Configuration
   embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
   entity_llm_model: "google/gemini-flash-1.5"
   answer_llm_model: "meta-llama/llama-3.3-70b-instruct:free"
     # Similarity Thresholds
   chunk_sim: 0.85
   entity_sim: 0.90
   graph_sim: 0.50
   
   # Search Parameters
   top_k: 100
   top_k_rerank: 15
   max_context_fraction: 0.4
   
   # System Settings
   log_level: "INFO"
   history_limit: 15
   ```

2. Load the configuration:
   ```python
   from backend.app.core.config import get_config
   cfg = get_config("config.yaml")
   ```

## Configuration Parameters

### API Keys

| Parameter | Description | Web UI | .env | YAML |
|-----------|-------------|--------|------|------|
| `OPENROUTER_API_KEY` | OpenRouter API key for LLM access | ✅ | ✅ | ✅ |

### Model Configuration

| Parameter | Description | Default Value |
|-----------|-------------|---------------|
| `EMBEDDING_MODEL` | Sentence transformer model | `sentence-transformers/all-MiniLM-L6-v2` |
| `RERANKER_MODEL` | Cross-encoder reranking model | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| `ENTITY_LLM_MODEL` | LLM for entity extraction | `google/gemini-flash-1.5` |
| `ANSWER_LLM_MODEL` | LLM for answer generation | `meta-llama/llama-3.3-70b-instruct:free` |
| `TRANSLATE_LLM_MODEL` | LLM for translation | `mistralai/mistral-nemo:free` |

### Similarity Thresholds

| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| `CHUNK_SIM` | Chunk similarity threshold | `0.85` | `0.0-1.0` |
| `ENTITY_SIM` | Entity similarity threshold | `0.90` | `0.0-1.0` |
| `GRAPH_SIM` | Graph similarity threshold | `0.82` | `0.0-1.0` |

### Search Parameters

| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| `TOP_K` | Initial retrieval count | `100` | `1-500` |
| `TOP_K_RERANK` | Final results after reranking | `15` | `1-50` |
| `MAX_CONTEXT_FRACTION` | Max context in LLM prompt | `0.4` | `0.1-0.8` |

### System Settings

| Parameter | Description | Default | Options |
|-----------|-------------|---------|---------|
| `LOG_LEVEL` | Logging verbosity | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `HISTORY_LIMIT` | Query history limit | `15` | `1-100` |
| `SAVED_LIMIT` | Saved documents limit | `15` | `1-100` |
| `SPACY_MODEL` | spaCy language model | `en_core_web_sm` | Any spaCy model |

### Directory Paths

| Parameter | Description | Default |
|-----------|-------------|---------|
| `BASE_DIR` | Project root directory | Auto-detected |
| `INPUT_DIR` | Input documents directory | `./input` |
| `SAVED_DIR` | Saved files directory | `./saved` |
| `VECTOR_DIR` | Vector store directory | `./vector_store` |
| `GRAPH_DB` | SQLite database path | `./data/graph.db` |

## Configuration Validation

### Web Interface Validation

The web interface provides real-time validation:
- ✅ **Green checkmark**: Configuration is valid and active
- ❌ **Red X**: Configuration is missing or invalid
- 🔄 **Spinner**: Configuration is being updated

### API Key Validation

Test your OpenRouter API key:

```bash
# Check configuration status
curl http://127.0.0.1:8000/api/admin/config

# Expected response for valid key:
{
  "config_values": {
    "openrouter_api_key_configured": true,
    ...
  }
}
```

### Health Check

Verify all components are working:

```bash
# System health check
curl http://127.0.0.1:8000/api/admin/health

# Expected response:
{
  "status": "healthy",
  "components": {
    "llm_client": {"status": "healthy", "provider": "OpenRouter"},
    ...
  }
}
```

## Configuration Best Practices

### Security

1. **Never commit API keys** to version control
2. **Use environment variables** for sensitive data
3. **Rotate API keys** regularly
4. **Use minimal permissions** for API keys

### Performance Tuning

1. **Adjust similarity thresholds** based on your use case:
   - Higher values = more precise, fewer results
   - Lower values = more recall, potentially noisy results

2. **Optimize search parameters**:
   - `TOP_K`: Start with 100, increase for better recall
   - `TOP_K_RERANK`: Start with 15, adjust based on response time
   - `MAX_CONTEXT_FRACTION`: Keep between 0.3-0.5 for optimal results

3. **Monitor resource usage**:
   ```bash
   # Get system metrics
   curl http://127.0.0.1:8000/api/admin/metrics
   ```

### Development vs Production

**Development Configuration:**
```properties
LOG_LEVEL=DEBUG
TOP_K=50
TOP_K_RERANK=10
```

**Production Configuration:**
```properties
LOG_LEVEL=INFO
TOP_K=100
TOP_K_RERANK=15
MAX_CONTEXT_FRACTION=0.4
```

## Troubleshooting

### Common Issues

1. **API Key Not Working**
   - Verify key format: `sk-or-v1-...`
   - Check key permissions on OpenRouter dashboard
   - Test with a simple API call

2. **Configuration Not Applied**
   - For `.env` changes: Restart the server
   - For web interface changes: Should apply immediately
   - Check logs for error messages

3. **Performance Issues**
   - Reduce `TOP_K` and `TOP_K_RERANK` values
   - Increase similarity thresholds
   - Monitor system metrics

### Debug Mode

Enable detailed logging:

1. **Via Web Interface:**
   - Go to Settings → System Configuration
   - Update LOG_LEVEL to "DEBUG"

2. **Via Environment:**
   ```bash
   export LOG_LEVEL=DEBUG
   python -m backend.app.main
   ```

3. **Via Configuration File:**
   ```yaml
   log_level: "DEBUG"
   ```

### Configuration Reset

To reset configuration to defaults:

1. **Delete configuration files:**
   ```bash
   rm .env config.yaml
   ```

2. **Clear cached configuration:**
   ```bash
   # Restart the application
   python -m backend.app.main
   ```

3. **Verify reset:**
   ```bash
   curl http://127.0.0.1:8000/api/admin/config
   ```

## Advanced Configuration

### Custom Model Integration

To use custom models, update the configuration:

```yaml
# Custom embedding model
embedding_model: "custom/embedding-model"

# Custom LLM models
entity_llm_model: "custom/entity-model"
answer_llm_model: "custom/answer-model"
```

### Multi-Environment Setup

Use different configurations for different environments:

```bash
# Development
python -m backend.app.main --config config.dev.yaml

# Staging
python -m backend.app.main --config config.staging.yaml

# Production
python -m backend.app.main --config config.prod.yaml
```

### Configuration API

Programmatically manage configuration:

```python
from backend.app.core.config import get_config

# Get current configuration
cfg = get_config()
print(f"Current TOP_K: {cfg.TOP_K}")

# Load custom configuration
cfg = get_config("custom_config.yaml")
print(f"Custom TOP_K: {cfg.TOP_K}")
```

## Migration Guide

### From Manual .env to Web Interface

1. **Backup existing configuration:**
   ```bash
   cp .env .env.backup
   ```

2. **Start application with existing config:**
   ```bash
   python -m backend.app.main
   ```

3. **Verify configuration status:**
   - Open `http://127.0.0.1:8000/settings`
   - Check that current API key shows as "Configured"

4. **Optional: Update via web interface:**
   - Click "Configure/Update" to change the key
   - System will update the same `.env` file

### From Legacy Configuration

If upgrading from an older version:

1. **Check for deprecated parameters:**
   ```bash
   # Review your current .env file
   cat .env
   ```

2. **Update parameter names** if needed (see current parameter list above)

3. **Test configuration:**
   ```bash
   curl http://127.0.0.1:8000/api/admin/health
   ```

## Support

For configuration issues:

1. **Check the logs** for detailed error messages
2. **Verify API keys** on the provider's dashboard
3. **Test configuration** using the health check endpoint
4. **Consult troubleshooting** section above

The web-based configuration interface makes setup easier than ever, while still providing full flexibility for advanced users who prefer file-based configuration.

