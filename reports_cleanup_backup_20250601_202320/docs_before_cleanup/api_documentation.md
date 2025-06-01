# SocioRAG Unified API Reference

## Overview
The SocioRAG API provides comprehensive endpoints for question-answering, document analysis, and social dynamics exploration. This unified reference combines detailed endpoint documentation with usage examples.

## Base URL
`
http://localhost:8000
`

## Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Authentication
Currently, all endpoints are publicly accessible. Authentication will be implemented in future versions.

## Core API Endpoints

### Question & Answer Endpoints

#### POST /api/qa/ask
Ask a question and receive a complete answer with citations.

**Request Body:**
`json
{
  "query": "What are the main themes in the documents?",
  "translate_to_arabic": false,
  "top_k": 5,
  "top_k_r": 3,
  "temperature": 0.7,
  "answer_model": "",
  "max_tokens": 4000,
  "context_window": 128000
}
`

**Response:**
`json
{
  "response": "Based on the documents...",
  "sources": [...],
  "query_id": "uuid-string",
  "processing_time": 2.5
}
`

#### GET /api/qa/history
Retrieve query history with optional filtering.

**Parameters:**
- limit (optional): Number of results (default: 50)
- offset (optional): Pagination offset (default: 0)

### Document Management Endpoints

#### POST /api/ingest/upload
Upload a PDF file for processing.

**Request:** Multipart form with file upload
**Response:** Processing status and document ID

#### POST /api/ingest/reset
Reset the corpus by clearing all data stores.

**Response:** Confirmation of reset operation

#### GET /api/documents/
List all processed documents with metadata.

### Administrative Endpoints

#### GET /api/admin/health
System health check with component status.

#### GET /api/admin/config
Retrieve current system configuration.

#### POST /api/admin/config
Update system configuration values.

### Search Endpoints

#### POST /api/search/semantic
Perform semantic search across document corpus.

**Request Body:**
`json
{
  "query": "search terms",
  "top_k": 10,
  "threshold": 0.7
}
`

## Usage Examples

### Complete Q&A Workflow
`python
import httpx

# 1. Upload document
with open("document.pdf", "rb") as f:
    response = httpx.post(
        "http://localhost:8000/api/ingest/upload",
        files={"file": f}
    )

# 2. Ask question
question_data = {
    "query": "What are the main themes?",
    "top_k": 5,
    "temperature": 0.7
}
response = httpx.post(
    "http://localhost:8000/api/qa/ask",
    json=question_data
)

# 3. Get history
history = httpx.get("http://localhost:8000/api/qa/history")
`

### Error Handling
All endpoints return standard HTTP status codes:
- 200: Success
- 400: Bad Request (invalid parameters)
- 404: Not Found
- 422: Validation Error
- 500: Internal Server Error

Error responses include detailed messages:
`json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE"
}
`

## Rate Limiting
Currently no rate limiting is implemented. This will be added in future versions for production deployments.

## WebSocket Support (Future)
Real-time updates and streaming responses will be available in future API versions.

---
*This unified reference consolidates information from multiple API documentation files for easier maintenance and user reference.*
