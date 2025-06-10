# SocioRAG

![SocioRAG Logo](resources/socioRAG-logo-small.png)

## 📈 Project Status

[![Status](resources/status-badge.png)](docs/project_status.md)
[![Version](resources/version-badge.png)](docs/project_status.md)

## ✅ Production Ready

- **0% Error Rate**: All tests passing, robust error handling
- **Sub-millisecond Response**: Optimized for speed and concurrency
- **Comprehensive Documentation**: All guides consolidated and up-to-date (June 2025)
- **Full Feature Set**: Entity extraction, vector search, multilingual support, PDF export, and analytics

## 🔑 Environment Variables

| Key                | Description                       | Example     |
| ------------------ | --------------------------------- | ----------- |
| OPENROUTER_API_KEY | LLM access key                    | `sk-or-***` |
| CHUNK_SIM          | Similarity threshold for chunking | `0.80`      |
| LOG_LEVEL          | Logging level                     | `DEBUG`     |
| ...                | ...                               | ...         |

See `.env.example` for the full list.

## 📋 Overview

SocioRAG is a production-ready system for analyzing social dynamics in texts through advanced NLP, entity extraction, vector search, and answer generation capabilities. The system follows a modular architecture with distinct phases for data ingestion, storage, retrieval, and answer generation.

### 🛡️ System Requirements

- **Python**: 3.8+ (with pip)
- **Node.js**: 18+ (with npm)
- **Operating System**: Windows (PowerShell), Linux/macOS (with minor script modifications)
- **Memory**: 4GB+ RAM recommended
- **Storage**: 2GB+ free space

### 🔄 Auto-Install Features

- **Smart Dependency Detection**: Automatically detects missing `node_modules` and installs frontend dependencies
- **Package Manager Support**: Works with npm, pnpm, or yarn (auto-detected)
- **Windows Path Handling**: Properly handles paths with spaces (e.g., "Program Files")
- **Robust Error Handling**: Clear error messages and automatic fallbacks
- **Zero Configuration**: Works out-of-the-box after environment setup

📖 **Complete guide**: [DEPLOYMENT.md](DEPLOYMENT.md)

## 🚀 Quick Start

> **🎯 TL;DR**:
>
> 1. Run `.\start.ps1`
> 2. When it says "Both services are healthy", click: [http://localhost:3000](http://localhost:3000)
> 3. When done, run `.\stop.ps1`

### ⚡ Instant Setup (Recommended)

```powershell
# Clone the repository
git clone https://github.com/Muhanad-husn/sociorag.git
cd sociorag

# Set up environment files
cp .env.example .env
cp config.yaml.example config.yaml

# Start the application - dependencies install automatically!
.\start.ps1
```

**That's it!** The startup script automatically:

- ✅ Detects missing dependencies and installs them
- ✅ Starts both backend and frontend services
- ✅ Waits for services to be healthy
- ✅ Shows "Both services are healthy" when ready

**📱 Once you see "Both services are healthy", click: [http://localhost:3000](http://localhost:3000)**

### 🔧 First-time Complete Setup (Optional)

For a complete environment setup including database initialization:

```powershell
# Run the comprehensive setup script
.\setup.ps1

# Then start normally
.\start.ps1
```

### 🖥️ Manual Setup (Advanced)

```powershell
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install frontend dependencies
cd ui
npm install
cd ..

# 3. Start services manually
# Terminal 1 - Backend
python -m backend.app.main

# Terminal 2 - Frontend
cd ui
npm run dev
```

### 🌐 Access Points

**After the startup script completes and shows "Both services are healthy", access the application at:**

- **🌟 Main Application**: **`http://localhost:3000`** ← **Click here to use SocioRAG!**
- **Backend API**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs`
- **Admin Panel**: `http://localhost:8000/api/admin/status`

> **💡 Note**: Wait for the startup script to finish loading before clicking the link. The application will automatically open in your browser when ready.

📖 **Full deployment guide**: [DEPLOYMENT.md](DEPLOYMENT.md)

## ✨ Feature Overview

| Feature              | Description                                                              | Status  |
| -------------------- | ------------------------------------------------------------------------ | ------- |
| Entity Extraction    | LLM-powered, multilingual                                                | ✅ Ready |
| Vector Search        | Fast, reranking, configurable; supports both chunk and entity embeddings | ✅ Ready |
| PDF Export           | Custom, styled, automated                                                | ✅ Ready |
| Query Analytics      | JSONL logs, performance metrics                                          | ✅ Ready |
| Multilingual Support | English & Arabic, translation API                                        | ✅ Ready |
| UI                   | Modern, responsive, bilingual                                            | ✅ Ready |
| Logging & Monitoring | Structured logs, REST API, health checks                                 | ✅ Ready |

## 🧪 Running Tests

```powershell
pytest tests/ -v          # run all tests
pytest -m integration -v  # integration tests only
```

Full guide: [tests/README.md](tests/README.md)

## 📊 Performance & Monitoring

See the performance dashboard setup in [instructions/readme/README.md](instructions/readme/README.md#performance-testing--monitoring).

## 🧹 Workspace Housekeeping

Recommended cleanup steps: [docs/production_deployment_guide.md](docs/production_deployment_guide.md#🧹-additional-cleanup-opportunities).

## 🏗️ How It Works

1. **Ingest**: Upload documents (PDF, text)
2. **Extract**: Entities and relationships via LLM + spaCy
3. **Store**:
   - Document chunks as vector embeddings for semantic retrieval
   - Entities as separate vector embeddings for entity-level search and graph analysis
   - **Semantic Chunking**: Intelligently divides text based on semantic boundaries rather than arbitrary length, with adaptive parameters for different document types and fallback mechanisms
4. **Query**: Semantic search and answer generation using both chunk and entity vectors
5. **Export**: Download answers and reports as PDF

## 🖥️ User Interface

- **Query History**: View, copy, and delete previous queries
- **Search**: Natural language, semantic, and multilingual
- **Document Management**: Upload, process, and download documents
- **Settings**: API keys, model selection, theme toggle, and performance metrics

## 📚 Documentation

- [Documentation Hub](docs/README.md) – Centralized access to all guides
- [Quick Start Guide](docs/installation_guide.md) – Fast onboarding
- [Unified API Reference](docs/api_documentation.md) – All endpoints and usage
- [Production Deployment Guide](docs/production_deployment_guide.md) – Deployment & runtime
- [Project Status Dashboard](docs/project_status.md) – Version, health, and changelog

## ⚡ Getting Started

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
.\start.ps1
# Or start with monitoring dashboard
# .\start.ps1 -EnableMonitoring
```

### Access Points

- Backend: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## 💻 Installation

### System Requirements

#### Minimum Requirements

- **Operating System**: Windows 11 (tested and verified), Windows 10, macOS 10.15+, or Linux (Ubuntu 18.04+) - *We welcome testing and feedback on other operating systems*
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

### 🚀 Starting the Application

```powershell
# Start in production mode
.\start.ps1

# Start with monitoring dashboard
.\start.ps1 -EnableMonitoring
```

**➡️ After startup completes, visit: [http://localhost:3000](http://localhost:3000)**

### 🛑 Stopping the Application

**⚠️ IMPORTANT**: Always properly shutdown the application when finished:

```powershell
# Stop the application (REQUIRED when done)
.\stop.ps1
```

> **💡 Why shutdown is important**: This script safely stops both backend and frontend services, prevents resource conflicts, and ensures clean shutdown of all processes.

### API Endpoints

The SocioRAG API provides endpoints for:

- Document ingestion and processing
- Query and answer generation
- PDF report export
- Query history and analytics

Full API documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) when the application is running.

## 🏗️ Architecture

Detailed diagrams & component docs → [docs/architecture_documentation.md](docs/architecture_documentation.md)

### Core Components

1. **Data Ingestion Pipeline** (`backend/app/ingest/`)
   - Enhanced entity extraction with LLM-powered analysis
   - Document chunking and metadata extraction
2. **Vector Storage & Retrieval** (`backend/app/retriever/`)
   - **Chunk Embeddings**: Stores document segments as vectors for semantic search (e.g., SQLite-vec)
   - **Entity Embeddings**: Stores named entities as separate vectors for entity-level similarity and graph operations
   - **Advanced Retrieval System**: Employs hybrid retrieval combining vector similarity, BM25 keyword matching, and cross-encoder reranking for comprehensive coverage
   - **Intelligent Context Management**: Dynamically balances relevance, diversity, and token limits with priority-based selection and semantic deduplication
   - Enables both chunk-based and entity-based retrieval with source diversity enforcement
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
- **Vector Database**: SQLite-vec for similarity search (chunks and entities)
- **Graph Database**: SQLite for entity relationships
- **Entity Extraction**: spaCy + Custom LLM pipeline
- **PDF Generation**: Playwright with browser automation

## 🤝 Support & Contributing

- Issue tracker → GitHub
- Contribution workflow → [Developer Guide](docs/guides/developer_guide.md#contributing-guidelines)
- CI/CD roadmap → [Project Status](docs/project_status.md#🔄-future-version-control-strategy)
- **Contact**: [Project Status Dashboard](docs/project_status.md) for updates and support links

## 📄 License

Apache-2.0 – see [LICENSE](LICENSE) for full terms.

## 🖼️ Demo & Screenshots

*TODO: Add screenshots or a demo GIF here to showcase the UI and features.*

## 🙏 Acknowledgements

- LangChain for LLM integration
- FastAPI for the web framework
- SQLite-vec for vector storage
- spaCy for NLP processing
