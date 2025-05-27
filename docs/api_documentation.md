# SocioGraph API Documentation

## Overview

The SocioGraph API provides comprehensive endpoints for question-answering, document analysis, and social dynamics exploration. The API is built with FastAPI and supports real-time streaming responses, file uploads, and PDF export functionality.

## Base URL

```
http://localhost:8000
```

## API Endpoints

### Question & Answer Endpoints

#### POST /api/qa/ask
Ask a question and receive a streaming answer with citations.

**Request Body:**
```json
{
  "question": "What are the main themes in the documents?",
  "include_citations": true
}
```

**Response:** Server-Sent Events (SSE) stream
```
data: {"type": "token", "content": "Based"}
data: {"type": "token", "content": " on"}
data: {"type": "token", "content": " the"}
data: {"type": "citation", "content": "[1]"}
data: {"type": "done", "content": ""}
```

**Event Types:**
- `token`: Individual token from the LLM response
- `citation`: Numbered citation reference
- `done`: End of response stream

**Example Usage:**
```javascript
const eventSource = new EventSource('/api/qa/ask', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    question: "What are the key relationships?",
    include_citations: true
  })
});

eventSource.onmessage = function(event) {
  const data = JSON.parse(event.data);
  if (data.type === 'token') {
    // Append token to answer
    answer += data.content;
  } else if (data.type === 'citation') {
    // Handle citation display
    citations.push(data.content);
  }
};
```

#### GET /api/qa/history
Retrieve query history with optional pagination.

**Query Parameters:**
- `limit` (optional): Number of entries to return (default: 50)
- `offset` (optional): Number of entries to skip (default: 0)

**Response:**
```json
{
  "history": [
    {
      "timestamp": "2024-05-26T10:30:00Z",
      "question": "What are the main themes?",
      "answer": "The main themes include...",
      "sources_count": 5,
      "response_time": 2.34
    }
  ],
  "total_count": 150,
  "has_more": true
}
```

#### GET /api/qa/stats
Get query statistics and analytics.

**Response:**
```json
{
  "total_queries": 150,
  "avg_response_time": 2.45,
  "total_sources_used": 750,
  "queries_today": 25,
  "most_common_topics": [
    {"topic": "relationships", "count": 45},
    {"topic": "themes", "count": 32}
  ]
}
```

### Document Management Endpoints

#### POST /api/documents/upload
Upload documents for processing and analysis.

**Request:** Multipart form data
```
Content-Type: multipart/form-data

file: <document_file>
metadata: {"title": "Document Title", "author": "Author Name"}
```

**Response:**
```json
{
  "success": true,
  "document_id": "doc_123456",
  "message": "Document uploaded and processed successfully",
  "entities_extracted": 45,
  "chunks_created": 12
}
```

#### GET /api/documents/{document_id}
Retrieve document information and metadata.

**Response:**
```json
{
  "document_id": "doc_123456",
  "title": "Document Title",
  "author": "Author Name",
  "upload_date": "2024-05-26T10:30:00Z",
  "status": "processed",
  "entities_count": 45,
  "chunks_count": 12,
  "file_size": 1024000
}
```

#### GET /api/documents
List all uploaded documents with filtering options.

**Query Parameters:**
- `status` (optional): Filter by processing status
- `limit` (optional): Number of documents to return
- `offset` (optional): Number of documents to skip

**Response:**
```json
{
  "documents": [
    {
      "document_id": "doc_123456",
      "title": "Document Title",
      "status": "processed",
      "upload_date": "2024-05-26T10:30:00Z"
    }
  ],
  "total_count": 10,
  "has_more": false
}
```

### Export Endpoints

#### POST /api/export/pdf
Generate and download a PDF report of Q&A session.

**Request Body:**
```json
{
  "question": "What are the main themes?",
  "answer": "The main themes include social dynamics, relationships...",
  "sources": [
    {"title": "Document 1", "content": "Relevant excerpt..."},
    {"title": "Document 2", "content": "Another excerpt..."}
  ]
}
```

**Response:** PDF file download
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="sociograph_report_20240526_103000.pdf"

<PDF binary data>
```

#### GET /api/export/history/{format}
Export query history in various formats.

**Path Parameters:**
- `format`: Export format (json, csv, xlsx)

**Query Parameters:**
- `start_date` (optional): Start date for export range
- `end_date` (optional): End date for export range

**Response:** File download in requested format

### Search Endpoints

#### GET /api/search/entities
Search for entities in the knowledge base.

**Query Parameters:**
- `q`: Search query
- `type` (optional): Entity type filter (PERSON, ORGANIZATION, etc.)
- `limit` (optional): Number of results to return

**Response:**
```json
{
  "entities": [
    {
      "name": "John Doe",
      "type": "PERSON",
      "confidence": 0.95,
      "occurrences": 15,
      "related_entities": ["Company ABC", "Project X"]
    }
  ],
  "total_count": 5
}
```

#### GET /api/search/relationships
Search for relationships between entities.

**Query Parameters:**
- `entity1` (optional): First entity name
- `entity2` (optional): Second entity name
- `relationship_type` (optional): Type of relationship

**Response:**
```json
{
  "relationships": [
    {
      "entity1": "John Doe",
      "entity2": "Company ABC",
      "relationship": "works_for",
      "confidence": 0.88,
      "source_documents": ["doc_123", "doc_456"]
    }
  ],
  "total_count": 3
}
```

### Static File Endpoints

#### GET /static/{filename}
Serve static files (CSS, JS, images, generated PDFs).

**Example:**
```
GET /static/pdf_theme.css
GET /static/generated_reports/report_123.pdf
```

## Error Handling

### Standard Error Response
```json
{
  "error": true,
  "message": "Description of the error",
  "error_code": "SPECIFIC_ERROR_CODE",
  "details": {
    "field": "Additional error details"
  }
}
```

### Common Error Codes
- `QUESTION_REQUIRED`: Question parameter is missing
- `DOCUMENT_NOT_FOUND`: Requested document doesn't exist
- `PROCESSING_ERROR`: Error during document processing
- `INVALID_FORMAT`: Unsupported file format
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `SERVER_ERROR`: Internal server error

## Rate Limiting

The API implements rate limiting to ensure fair usage:
- **Standard endpoints**: 100 requests per minute
- **Upload endpoints**: 10 requests per minute
- **Export endpoints**: 5 requests per minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Authentication

### API Key Authentication (Future Implementation)
```
Authorization: Bearer your_api_key_here
```

### Session-based Authentication (Future Implementation)
```
Cookie: session_id=your_session_id
```

## WebSocket Support (Future Implementation)

### Real-time Q&A WebSocket
```
ws://localhost:8000/ws/qa
```

**Message Format:**
```json
{
  "type": "question",
  "question": "What are the main themes?",
  "include_citations": true
}
```

## SDK Examples

### Python SDK
```python
import requests
import json

class SocioGraphClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def ask_question(self, question, include_citations=True):
        response = requests.post(
            f"{self.base_url}/api/qa/ask",
            json={
                "question": question,
                "include_citations": include_citations
            },
            stream=True
        )
        
        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode('utf-8').replace('data: ', ''))
                yield data
    
    def get_history(self, limit=50, offset=0):
        response = requests.get(
            f"{self.base_url}/api/qa/history",
            params={"limit": limit, "offset": offset}
        )
        return response.json()

# Usage
client = SocioGraphClient()
for token in client.ask_question("What are the main themes?"):
    if token['type'] == 'token':
        print(token['content'], end='')
```

### JavaScript SDK
```javascript
class SocioGraphClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async askQuestion(question, includeCitations = true) {
        const response = await fetch(`${this.baseUrl}/api/qa/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question,
                include_citations: includeCitations
            })
        });
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.substring(6));
                    yield data;
                }
            }
        }
    }
    
    async getHistory(limit = 50, offset = 0) {
        const response = await fetch(
            `${this.baseUrl}/api/qa/history?limit=${limit}&offset=${offset}`
        );
        return response.json();
    }
}

// Usage
const client = new SocioGraphClient();

async function askQuestion() {
    for await (const token of client.askQuestion("What are the main themes?")) {
        if (token.type === 'token') {
            document.getElementById('answer').innerHTML += token.content;
        }
    }
}
```

## Testing the API

### Using curl
```bash
# Ask a question
curl -X POST "http://localhost:8000/api/qa/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the main themes?", "include_citations": true}'

# Get history
curl "http://localhost:8000/api/qa/history?limit=10"

# Get statistics
curl "http://localhost:8000/api/qa/stats"

# Upload document
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@document.pdf" \
  -F 'metadata={"title": "Test Document"}'
```

### Using Postman
1. Import the SocioGraph API collection
2. Set base URL to `http://localhost:8000`
3. Configure environment variables for testing
4. Run automated test suites

## Performance Considerations

### Response Times
- **Simple Q&A**: 1-3 seconds average
- **Complex Q&A with citations**: 3-5 seconds average
- **Document upload**: 5-30 seconds depending on size
- **PDF generation**: 2-5 seconds average

### Optimization Tips
1. Use streaming for real-time user feedback
2. Implement client-side caching for static data
3. Batch multiple requests when possible
4. Use appropriate timeout values
5. Implement retry logic for transient failures

## Troubleshooting

### Common Issues
1. **Connection errors**: Check if the server is running
2. **Timeout errors**: Increase client timeout values
3. **Memory errors**: Reduce batch sizes for large operations
4. **PDF generation fails**: Ensure WeasyPrint dependencies are installed

### Debug Mode
Enable debug logging by setting `LOG_LEVEL=DEBUG` in configuration:
```bash
export LOG_LEVEL=DEBUG
python -m backend.app.main
```

## Administrative API Endpoints

### System Health Check

#### GET /api/admin/health
Get comprehensive system health status and component diagnostics.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-05-27T16:45:00Z",
  "version": "0.1.0",
  "uptime": 3600.5,
  "components": {
    "database": {
      "status": "healthy",
      "type": "SQLite"
    },
    "vector_store": {
      "status": "healthy",
      "type": "ChromaDB",
      "document_count": 25
    },
    "embedding_service": {
      "status": "healthy",
      "model": "sentence-transformers",
      "embedding_dim": 384
    },
    "llm_client": {
      "status": "healthy",
      "provider": "OpenRouter"
    }
  }
}
```

### System Metrics

#### GET /api/admin/metrics
Get detailed system performance metrics including CPU, memory, and disk usage.

**Response:**
```json
{
  "cpu_usage": 15.2,
  "memory_usage": {
    "total_gb": 16.0,
    "available_gb": 8.5,
    "used_gb": 7.5,
    "percentage": 46.9
  },
  "disk_usage": {
    "total_gb": 500.0,
    "free_gb": 250.0,
    "used_gb": 250.0,
    "percentage": 50.0
  },
  "database_stats": {
    "entity_count": 1250,
    "relation_count": 890,
    "documents_count": 25,
    "file_size_mb": 12.5
  },
  "vector_store_stats": {
    "document_count": 25,
    "storage_size_mb": 45.2
  },
  "timestamp": "2025-05-27T16:45:00Z"
}
```

### System Configuration

#### GET /api/admin/config
Get current system configuration including API key status.

**Response:**
```json
{
  "config_values": {
    "input_dir": "/path/to/input",
    "saved_dir": "/path/to/saved",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "entity_llm_model": "google/gemini-flash-1.5",
    "openrouter_api_key_configured": true,
    "chunk_similarity": 0.85,
    "top_k": 100,
    "log_level": "INFO"
  },
  "config_source": "environment variables and defaults",
  "last_modified": null
}
```

### API Key Management

#### PUT /api/admin/api-keys
Update API keys with automatic persistence to .env file and configuration reload.

**Request Body:**
```json
{
  "openrouter_api_key": "sk-or-v1-your-api-key-here"
}
```

**Response:**
```json
{
  "success": true,
  "message": "API keys updated successfully: OPENROUTER_API_KEY",
  "data": {
    "updated_keys": ["OPENROUTER_API_KEY"],
    "env_file": "/path/to/.env"
  }
}
```

**Features:**
- Automatically updates `.env` file
- Clears configuration cache for immediate effect
- Resets LLM client to use new API key
- Supports removing API key by sending empty string
- No server restart required

**Example Usage:**

**Setting an API Key:**
```bash
curl -X PUT "http://127.0.0.1:8000/api/admin/api-keys" \
  -H "Content-Type: application/json" \
  -d '{"openrouter_api_key":"sk-or-v1-your-api-key"}'
```

**Removing an API Key:**
```bash
curl -X PUT "http://127.0.0.1:8000/api/admin/api-keys" \
  -H "Content-Type: application/json" \
  -d '{"openrouter_api_key":""}'
```

### System Maintenance

#### POST /api/admin/maintenance/cleanup
Perform system cleanup and optimization tasks.

**Response:**
```json
{
  "operation": "system_cleanup",
  "success": true,
  "details": {
    "cleaned_files": 15,
    "database_optimized": true,
    "vector_store_checked": true,
    "memory_cleanup": true
  },
  "duration": 2.34
}
```

### System Logs

#### GET /api/admin/logs
Get recent system log entries with optional filtering.

**Query Parameters:**
- `lines` (optional): Number of log lines to return (default: 100)
- `level` (optional): Log level filter (default: "INFO")

**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2025-05-27T16:45:00Z",
      "level": "INFO",
      "message": "System is running normally",
      "module": "admin"
    }
  ],
  "total_lines": 1,
  "requested_lines": 100,
  "level_filter": "INFO"
}
```

This comprehensive API documentation provides all the necessary information for integrating with the SocioGraph system and building applications on top of the Q&A and document analysis capabilities.
