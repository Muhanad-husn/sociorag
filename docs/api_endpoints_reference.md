# SocioGraph API Endpoints Reference

This document provides a comprehensive reference of all API endpoints available in SocioGraph after the completion of Phase 6.

## Base URL

All API endpoints are relative to the base URL:

```
http://localhost:8000
```

## API Documentation

Interactive API documentation is available at:

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`

## Authentication

Authentication is not yet implemented in Phase 6. All endpoints are publicly accessible.

## Endpoints by Category

### Ingest API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/ingest/reset` | Reset the corpus by clearing all data stores |
| `POST` | `/api/ingest/upload` | Upload a PDF file for processing |
| `POST` | `/api/ingest/process` | Manually trigger processing of all files in the input directory |
| `GET`  | `/api/ingest/progress` | Stream progress updates from the ingestion pipeline (SSE) |

### Question & Answer API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/qa/ask` | Ask a question with streaming response (SSE) |
| `GET`  | `/api/qa/history` | Get recent Q&A history |
| `GET`  | `/api/qa/stats` | Get Q&A statistics |

### History API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/history/` | Get paginated history with search |
| `GET`  | `/api/history/stats` | Get history statistics |
| `GET`  | `/api/history/record/{record_id}` | Get a specific history record |
| `DELETE` | `/api/history/record/{record_id}` | Delete a specific history record |
| `DELETE` | `/api/history/clear` | Clear all history records |

### Admin API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/admin/health` | Get system health status and component diagnostics |
| `GET`  | `/api/admin/metrics` | Get system performance metrics (CPU, memory, disk) |
| `GET`  | `/api/admin/config` | Get current system configuration and API key status |
| `PUT`  | `/api/admin/config` | Update system configuration values |
| `PUT`  | `/api/admin/api-keys` | Update API keys (OpenRouter) with persistence to .env |
| `GET`  | `/api/admin/logs` | Get recent system log entries |
| `POST` | `/api/admin/maintenance/cleanup` | Perform system cleanup and optimization |
| `POST` | `/api/admin/restart` | Restart system components (development mode disabled) |

### Logs API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/logs/errors` | Get error summary and analysis with trends |
| `GET`  | `/api/logs/performance` | Get performance metrics and timing analysis |
| `GET`  | `/api/logs/user-activity` | Get user activity tracking and patterns |
| `GET`  | `/api/logs/health` | Get system health monitoring and status |
| `POST` | `/api/logs/search` | Search logs with filters and criteria |
| `GET`  | `/api/logs/correlation/{correlation_id}` | Trace all logs for a correlation ID |
| `POST` | `/api/logs/cleanup` | Cleanup old log files and manage retention |
| `GET`  | `/api/logs/stats` | Get comprehensive log statistics |

### WebSocket API

| Endpoint | Description |
|----------|-------------|
| `/api/ws/qa` | Real-time Q&A with token streaming |
| `/api/ws/processing/{document_id}` | Document processing status updates |
| `/api/ws/monitor` | System monitoring and notifications |

### Root Endpoint

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/` | Health check and API information |

### Static Files

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/static/saved/{filename}` | Access saved PDFs and other static files |

## Detailed Endpoint Documentation

### `/api/ingest/reset`

Reset the corpus by clearing all data stores.

**Request:**
```http
POST /api/ingest/reset
```

**Response:**
```json
{
  "status": "success",
  "message": "Corpus reset successfully"
}
```

### `/api/ingest/upload`

Upload a PDF file for processing.

**Request:**
```http
POST /api/ingest/upload
Content-Type: multipart/form-data

file=@path/to/document.pdf
```

**Response:**
```json
{
  "status": "uploaded",
  "file": "document.pdf",
  "message": "Processing started in the background"
}
```

### `/api/ingest/process`

Manually trigger processing of all files in the input directory.

**Request:**
```http
POST /api/ingest/process
```

**Response:**
```json
{
  "status": "started",
  "message": "Processing started in the background"
}
```

### `/api/ingest/progress`

Stream progress updates from the ingestion pipeline using Server-Sent Events (SSE).

**Request:**
```http
GET /api/ingest/progress
```

**Response (Stream):**
```
data: {"phase": "loading", "percent": 0, "file": "document.pdf"}

data: {"phase": "processing", "percent": 50, "file": "document.pdf", "chunks": 10}

data: {"phase": "complete", "percent": 100, "files": 1, "chunks": 20}

event: heartbeat
data: 1716743852.123

event: error
data: {"error": "Error message"}
```

### `/api/qa/ask`

Ask a question with streaming response using Server-Sent Events (SSE).

**Request:**
```http
POST /api/qa/ask
Content-Type: application/json

{
  "question": "What are the main themes in the document?"
}
```

**Response (Stream):**
```
event: start
data: Starting answer generation for: What are the main themes in the document?...

event: token
data: The

event: token
data: main

...

event: complete
data: {"pdf_url": "/static/saved/answer_20250526_123456.pdf", "token_count": 150, "duration": 2.5}
```

### `/api/history/`

Get paginated history with optional search filtering.

**Request:**
```http
GET /api/history/?page=1&per_page=10&search=climate
```

**Response:**
```json
{
  "records": [
    {
      "id": 1,
      "query": "What are the impacts of climate change?",
      "timestamp": "2025-05-26T10:00:00",
      "token_count": 150,
      "context_count": 5,
      "metadata": {}
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 10,
  "has_next": false,
  "has_prev": false
}
```

### `/api/history/record/{record_id}` - DELETE

Delete a specific history record by its ID.

**Request:**
```http
DELETE /api/history/record/5
```

**Response:**
```json
{
  "status": "success",
  "message": "History record 5 deleted successfully",
  "record_id": 5
}
```

**Error Response:**
```json
{
  "detail": "History record not found"
}
```

### `/api/history/clear` - DELETE

Clear all history records.

**Request:**
```http
DELETE /api/history/clear
```

**Response:**
```json
{
  "status": "success",
  "message": "All history records cleared (42 records removed)"
}
```

### WebSocket: `/api/ws/qa`

Real-time Q&A with token streaming via WebSocket.

**Connect:**
```
WebSocket connection to ws://localhost:8000/api/ws/qa
```

**Request Message:**
```json
{
  "type": "question",
  "question": "What are the main themes?",
  "session_id": "user_session_123"
}
```

**Response Messages:**
```json
{"type": "question_received", "session_id": "user_session_123", "question": "What are the main themes?"}

{"type": "status", "message": "Retrieving context..."}

{"type": "status", "message": "Generating answer...", "context_chunks": 5}

{"type": "token", "content": "The", "session_id": "user_session_123"}

{"type": "token", "content": " main", "session_id": "user_session_123"}

{"type": "answer_complete", "session_id": "user_session_123", "full_answer": "The main themes...", "context_count": 5, "timestamp": "2025-05-26T10:15:30"}
```

### `/api/logs/errors`

Get error summary and analysis with trends.

**Request:**
```http
GET /api/logs/errors?hours=24
```

**Parameters:**
- `hours` (optional): Number of hours to look back (default: 24)

**Response:**
```json
{
  "total_errors": 15,
  "error_rate": 0.02,
  "top_errors": [
    {
      "message": "Database connection failed",
      "count": 8,
      "level": "ERROR",
      "first_seen": "2024-01-15T10:00:00Z",
      "last_seen": "2024-01-15T14:30:00Z"
    }
  ],
  "error_trend": {
    "hourly_counts": [2, 1, 0, 3, 5, 2, 1, 1]
  }
}
```

### `/api/logs/performance`

Get performance metrics and timing analysis.

**Request:**
```http
GET /api/logs/performance?hours=1
```

**Parameters:**
- `hours` (optional): Number of hours to look back (default: 1)

**Response:**
```json
{
  "request_count": 1250,
  "avg_response_time": 245.7,
  "95th_percentile": 890.2,
  "slow_requests": 15,
  "endpoints": [
    {
      "path": "/api/qa/ask",
      "method": "POST",
      "avg_time": 1250.5,
      "request_count": 45
    }
  ]
}
```

### `/api/logs/health`

Get system health monitoring and status.

**Request:**
```http
GET /api/logs/health
```

**Response:**
```json
{
  "status": "healthy",
  "error_rate": 0.01,
  "avg_response_time": 234.5,
  "active_users": 12,
  "last_error": "2024-01-15T12:00:00Z",
  "uptime_hours": 168.5,
  "log_file_sizes": {
    "sociorag_main.log": 8.5,
    "sociorag_error.log": 2.1
  }
}
```

### `/api/logs/search`

Search logs with filters and criteria.

**Request:**
```http
POST /api/logs/search
Content-Type: application/json

{
  "query": "database error",
  "level": "ERROR",
  "start_time": "2024-01-15T00:00:00Z",
  "end_time": "2024-01-15T23:59:59Z",
  "limit": 100
}
```

**Response:**
```json
{
  "results": [
    {
      "timestamp": "2024-01-15T15:30:45.123Z",
      "level": "ERROR",
      "message": "Database connection failed",
      "correlation_id": "req_abc123",
      "extra": {
        "error_type": "ConnectionError",
        "retry_count": 3
      }
    }
  ],
  "total_count": 25,
  "query_time_ms": 45.2
}
```

### `/api/logs/correlation/{correlation_id}`

Trace all logs for a specific correlation ID.

**Request:**
```http
GET /api/logs/correlation/req_abc123def456
```

**Response:**
```json
[
  {
    "timestamp": "2024-01-15T15:30:45.123Z",
    "level": "INFO",
    "message": "Request started",
    "correlation_id": "req_abc123def456"
  },
  {
    "timestamp": "2024-01-15T15:30:46.789Z",
    "level": "DEBUG",
    "message": "Processing data",
    "correlation_id": "req_abc123def456"
  }
]
```

### `/api/logs/stats`

Get comprehensive log statistics.

**Request:**
```http
GET /api/logs/stats
```

**Response:**
```json
{
  "total_entries": 15420,
  "file_count": 5,
  "total_size_mb": 12.8,
  "oldest_entry": "2024-01-01T00:00:00Z",
  "newest_entry": "2024-01-15T15:30:00Z",
  "entries_by_level": {
    "INFO": 8950,
    "DEBUG": 4200,
    "WARNING": 1800,
    "ERROR": 420,
    "CRITICAL": 50
  }
}
```

## Error Responses

All API endpoints follow a consistent error response format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:

- `400 Bad Request` - Invalid input or parameters
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server-side error

## Conclusion

This API reference covers the endpoints implemented in Phase 6 of SocioGraph. The API provides comprehensive functionality for document ingestion, question answering, history management, and real-time communication.

Future phases will extend this API with additional endpoints for authentication, advanced search, and administrative functions.
