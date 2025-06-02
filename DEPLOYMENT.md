# SocioRAG Deployment Guide

## 🚀 Quick Start Deployment

### Prerequisites
- Python 3.8+
- Node.js 18+ (for UI development)
- Git

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

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize Database
```bash
python scripts/init_database_schema.py
```

### 5. Start Application
```bash
# Production (Windows)
.\start_production.ps1

# Development
python -m backend.app.main
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

### Common Issues
1. **Import Errors**: Ensure you're running from the project root
2. **API Key Issues**: Verify your OpenRouter API key is valid
3. **Permission Issues**: Check file permissions for database and logs
4. **Port Conflicts**: Default port is 8000, change in config if needed

### Support
- Check `docs/` for detailed documentation
- Review logs in `logs/` directory
- Run tests: `pytest tests/ -v`

## 🔒 Security Notes

- Never commit `.env` or `config.yaml` files
- Use environment variables in production
- Regularly rotate API keys
- Monitor logs for security events
