# SocioRAG Deployment Guide

## 🚀 Quick Start Deployment

### Prerequisites

- **Python 3.8+** (with pip)
- **Node.js 18+** (with npm) - automatically detected and used
- **Git**

### 1. Clone Repository

```bash
git clone https://github.com/your-username/sociorag.git
cd sociorag
```

### 2. Environment Setup

```bash
# Copy environment templates
cp .env.example .env
cp config.yaml.example config.yaml

# Edit with your actual values
# .env: OPENROUTER_API_KEY, CHUNK_SIM, LOG_LEVEL
# config.yaml: API keys, vector store path, similarity thresholds
```

### 3. Deploy Application

#### ⚡ Instant Deployment (Recommended)

```powershell
# Windows - Auto-installs all dependencies and starts services
.\start.ps1
```

The startup script automatically:

- ✅ Detects and installs missing Python dependencies
- ✅ Detects and installs missing frontend dependencies (npm/pnpm/yarn)
- ✅ Handles Windows paths with spaces properly
- ✅ Starts backend and frontend services
- ✅ Waits for services to be healthy
- ✅ Opens application in browser

#### 🔧 Complete Setup (First-time)

```powershell
# Comprehensive setup including database initialization
.\setup.ps1
```

#### 📋 Manual Setup (Advanced)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd ui
npm install
cd ..

# Initialize database (optional)
python scripts/init_database_schema.py

# Start services
python -m backend.app.main  # Terminal 1
cd ui && npm run dev        # Terminal 2
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
CHUNK_SIM=0.80
LOG_LEVEL=INFO  # Use INFO for production, DEBUG for development
```

### Application Config (config.yaml)

```yaml
chunk_sim: 0.8
top_k: 50
vector_dir: ./vector_store  # Adjust path for your deployment
openrouter_api_key: sk-or-v1-your-api-key-here
huggingface_token: hf_your-token-here  # Required for Arabic translation
```

## 🏗️ Architecture

- **Backend**: FastAPI (Python) - REST API and core logic
- **Frontend**: Modern HTML/CSS/JS - User interface
- **Database**: SQLite with vector extensions
- **Vector Store**: ChromaDB for embeddings
- **LLM**: OpenRouter API integration

## 📊 Monitoring

- **Logs**: `logs/` directory with structured logging
- **Health Check**: `http://localhost:8000/health`
- **API Docs**: `http://localhost:8000/docs`

## 🛠️ Troubleshooting

### Auto-Install Issues

1. **Node.js not found**: Ensure Node.js 18+ is installed and in PATH
2. **npm command fails**: Check if npm is properly installed with Node.js
3. **Permission errors**: Run PowerShell as Administrator if needed
4. **Path with spaces**: Auto-handled, but ensure proper quoting in manual commands
5. **Package manager detection**: Script auto-detects npm/pnpm/yarn based on lock files

### Common Issues

1. **Import Errors**: Ensure you're running from the project root
2. **API Key Issues**: Verify your OpenRouter API key is valid
3. **Permission Issues**: Check file permissions for database and logs
4. **Port Conflicts**: Default ports are 8000 (backend) and 5173 (frontend)
5. **Dependencies missing**: Use `.\setup.ps1` for complete environment setup

### Windows System Restart Recovery

After a Windows restart, simply run:

```powershell
.\start.ps1
```

The script will automatically detect and reinstall missing dependencies.

### Package Manager Support

- **npm**: Default, works out-of-the-box
- **pnpm**: Auto-detected if `pnpm-lock.yaml` exists
- **yarn**: Auto-detected if `yarn.lock` exists

### Support

- Check `docs/` for detailed documentation
- Review logs in `logs/` directory
- Run tests: `pytest tests/ -v`

## 🔒 Security Notes

- Never commit `.env` or `config.yaml` files
- Use environment variables in production
- Regularly rotate API keys
- Monitor logs for security events
