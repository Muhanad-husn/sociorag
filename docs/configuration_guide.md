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
   graph_sim: 0.95
   
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
| `GRAPH_SIM` | Graph similarity threshold | `0.95` | `0.0-1.0` |

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
