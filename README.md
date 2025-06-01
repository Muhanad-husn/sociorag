# SocioRAG

![SocioRAG Logo](resources/logo.png)

## Comprehensive system for analyzing and visualizing social dynamics in texts

## 📋 Overview

SocioRAG is a production-ready system for analyzing and visualizing social dynamics in texts through advanced NLP, entity extraction, vector search, and answer generation capabilities. The system follows a modular architecture with distinct phases for data ingestion, storage, retrieval, and answer generation.

## ✨ Key Features

- **Enhanced Entity Extraction**: LLM-powered entity and relationship extraction with multiple JSON parsing strategies
- **Advanced Vector Retrieval**: Semantic similarity search with reranking and configurable thresholds
- **Complete Answer Generation**: Comprehensive response generation with citation management
- **PDF Export System**: Professional PDF generation with custom styling and layout
- **Query History & Analytics**: JSONL-based append-only logging with performance metrics
- **Multilingual Support**: Including Arabic language processing and translation capabilities

## 🚀 Quick Start

### One-Command Setup

```powershell
# Automated setup - handles everything
.\quick_start.ps1
```

### Manual Quick Setup

```powershell
# 1. Create environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies  
pip install -r requirements.txt

# 3. Set up configuration
# Copy config.yaml.example to config.yaml and update with your API keys
Copy-Item config.yaml.example config.yaml
# Edit config.yaml with your OpenRouter API key and other settings

# 4. Start application
.\start_production.ps1
```

### Access Points

- Backend: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## 💻 Installation

### System Requirements

#### Minimum Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Python**: 3.12.9 (required for compatibility)
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 2GB free space for dependencies and models
- **Internet**: Required for model downloads and API access

#### Recommended Requirements

- **Memory**: 16GB RAM for optimal performance
- **Storage**: 10GB free space for large document processing
- **CPU**: Multi-core processor for concurrent processing
- **GPU**: Optional, for accelerated embeddings (future feature)

### Method 1: Conda Installation (Recommended)

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

# 5. Download required spaCy model (Conda)
python -m spacy download en_core_web_sm

# 6. Install Playwright browsers for PDF generation (Conda)
playwright install
```

### Method 2: pip Installation

Using pip with virtual environment for Python package management.

```bash
# 1. Clone the repository
git clone <repository-url>
cd sociorag

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate the environment

# On Windows
.\.venv\Scripts\Activate.ps1

# On macOS/Linux
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Download required spaCy model (pip)
python -m spacy download en_core_web_sm

# 6. Install Playwright browsers for PDF generation (pip)
playwright install
```

## 🛠️ Configuration

Copy the example configuration file and update with your settings:

```powershell
Copy-Item config.yaml.example config.yaml
```

Edit the `config.yaml` file with your specific configuration:

```yaml
chunk_sim: 0.8                               # Similarity threshold for chunking
top_k: 50                                    # Number of top results to retrieve
vector_dir: /path/to/vector_store            # Path to vector store directory
openrouter_api_key: sk-or-v1-your-api-key    # OpenRouter API key
huggingface_token: hf_your_token             # HuggingFace token for translation
```

## 🔄 Usage

### Starting the Application

```powershell
# Start in production mode
.\start_production.ps1

# Stop the application
.\stop_production.ps1
```

### API Endpoints

The SocioRAG API provides endpoints for:

- Document ingestion and processing
- Query and answer generation
- PDF report export
- Query history and analytics

Full API documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) when the application is running.

## 🏗️ Architecture

### Core Components

1. **Data Ingestion Pipeline** (`backend/app/ingest/`)
   - Enhanced entity extraction with LLM-powered analysis
   - Document chunking and metadata extraction
2. **Vector Storage & Retrieval** (`backend/app/retriever/`)
   - SQLite-vec based vector storage
   - Semantic search with reranking
3. **Answer Generation** (`backend/app/answer/`)
   - Complete response generation with LLM integration
   - Citation management and source linking
4. **Core Infrastructure** (`backend/app/core/`)
   - Centralized configuration management
   - Logging and error handling
5. **API Layer** (`backend/app/api/`)
   - FastAPI endpoints for Q&A functionality
   - RESTful interface design

### Technology Stack

- **Framework**: FastAPI with async/await support
- **LLM Integration**: LangChain with OpenRouter API
- **Vector Database**: SQLite-vec for similarity search
- **Graph Database**: SQLite for entity relationships
- **Entity Extraction**: spaCy + Custom LLM pipeline
- **PDF Generation**: Playwright with browser automation

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:

- [Installation Guide](docs/installation_guide.md) - Detailed setup instructions
- [API Documentation](docs/api_documentation.md) - Complete API reference
- [Project Overview](docs/project_overview.md) - System architecture and features
- [Architecture Documentation](docs/architecture_documentation.md) - Detailed system design
- [Production Deployment Guide](docs/production_deployment_guide.md) - Deployment instructions

## 🧪 Testing

Run tests using pytest:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/path/to/test_file.py
```

## 📄 License

[Add your license information here]

## 🙏 Acknowledgements

- LangChain for LLM integration
- FastAPI for the web framework
- SQLite-vec for vector storage
- spaCy for NLP processing
