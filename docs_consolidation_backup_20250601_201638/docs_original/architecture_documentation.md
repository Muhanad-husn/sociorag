# SocioGraph Architecture Documentation

## System Architecture Overview

SocioGraph is designed as a modular, scalable system for analyzing social dynamics in texts. The architecture follows a layered approach with clear separation of concerns, enabling maintainability, testability, and future extensibility.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Web UI    │  │ Mobile App  │  │  External Clients   │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/WebSocket/SSE
┌─────────────────────┴───────────────────────────────────────┐
│                   API Gateway                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              FastAPI Application                       │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │ │
│  │  │    Q&A   │ │Document  │ │  Search  │ │    Export    │ │ │
│  │  │Endpoints │ │Management│ │Endpoints │ │  Endpoints   │ │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘ │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │ Internal API Calls
┌─────────────────────┴───────────────────────────────────────┐
│                 Business Logic Layer                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │   Answer     │ │  Retriever   │ │    Ingestion         │ │
│  │ Generation   │ │   Module     │ │    Pipeline          │ │
│  └──────────────┘ └──────────────┘ └──────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │ Data Access
┌─────────────────────┴───────────────────────────────────────┐
│                   Data Layer                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │   Vector     │ │    Graph     │ │     File System      │ │
│  │   Store      │ │  Database    │ │     Storage          │ │
│  │ (SQLite-vec) │ │  (SQLite)    │ │   (Documents/PDFs)   │ │
│  └──────────────┘ └──────────────┘ └──────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. API Layer (`backend/app/api/`)

The API layer provides RESTful endpoints and real-time communication interfaces.

**Key Components:**
- **Q&A Router** (`qa.py`): Handles question-answering with streaming responses
- **Document Router** (future): Document upload and management
- **Search Router** (future): Entity and relationship search
- **Export Router** (future): PDF and data export functionality

**Technologies:**
- FastAPI for REST API framework
- Server-Sent Events (SSE) for real-time streaming
- Pydantic for request/response validation
- uvicorn for ASGI server

```python
# API Layer Structure
backend/app/api/
├── __init__.py           # API module initialization
├── qa.py                 # Q&A endpoints with SSE streaming
├── documents.py          # Document management (future)
├── search.py             # Search endpoints (future)
└── export.py             # Export endpoints (future)
```

### 2. Answer Generation Module (`backend/app/answer/`)

Handles the complete answer generation pipeline with streaming, citations, and export.

**Key Components:**
- **Prompt Builder** (`prompt.py`): Constructs system and user prompts
- **Generator** (`generator.py`): Streams LLM responses with citations
- **PDF Generator** (`pdf.py`): Creates formatted PDF reports
- **History Tracker** (`history.py`): Logs queries and generates analytics

**Data Flow:**
1. Question received → Prompt construction
2. Context retrieval → Prompt enhancement
3. LLM streaming → Token-by-token response
4. Citation injection → Source linking
5. History logging → Analytics update

```python
# Answer Module Architecture
backend/app/answer/
├── __init__.py           # Module exports
├── prompt.py             # Prompt building and templates
├── generator.py          # Streaming answer generation
├── pdf.py                # PDF export with WeasyPrint
└── history.py            # Query history and analytics
```

### 3. Retrieval System (`backend/app/retriever/`)

Manages document search, context retrieval, and relevance ranking.

**Key Components:**
- **Vector Search**: Semantic similarity using embeddings
- **Reranking**: Improves relevance with cross-encoder models
- **Context Assembly**: Combines multiple sources into coherent context
- **Caching**: Optimizes repeated queries

**Technologies:**
- SQLite-vec for vector storage and similarity search
- Sentence Transformers for embeddings
- Cross-encoder models for reranking
- LRU caching for performance optimization

### 4. Data Ingestion Pipeline (`backend/app/ingest/`)

Processes documents and extracts structured information for storage.

**Key Components:**
- **Document Parser**: Extracts text from various formats
- **Entity Extraction**: LLM-powered entity and relationship extraction
- **Chunking Strategy**: Intelligent text segmentation
- **Embedding Generation**: Vector representations for search

**Enhanced Features:**
- Retry mechanisms for API reliability
- Response caching for performance
- Batch processing with concurrency control
- Multiple JSON parsing strategies

### 5. Core Infrastructure (`backend/app/core/`)

Provides shared services and cross-cutting concerns.

**Key Components:**
- **Singleton Pattern**: Manages shared resources (DB, LLM, Logger)
- **Configuration Management**: Centralized settings with overrides
- **Logging System**: Structured logging with multiple levels
- **Database Connections**: Connection pooling and management

## Data Architecture

### Vector Storage Strategy

```
Document Processing Flow:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Raw Text   │───▶│   Chunks    │───▶│ Embeddings  │
└─────────────┘    └─────────────┘    └─────────────┘
                          │                    │
                          ▼                    ▼
                   ┌─────────────┐    ┌─────────────┐
                   │  Metadata   │    │SQLite-vec DB│
                   └─────────────┘    └─────────────┘
```

**Storage Schema:**
- **Chunks Table**: Text segments with metadata
- **Embeddings Table**: Vector representations
- **Documents Table**: Source document information
- **Index Table**: Efficient similarity search structures

### Graph Database Design

```
Entity-Relationship Model:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Entity    │───▶│Relationship │◀───│   Entity    │
│    Type     │    │    Type     │    │    Type     │
│  PERSON     │    │ WORKS_FOR   │    │ORGANIZATION │
│  LOCATION   │    │ LOCATED_IN  │    │  CONCEPT    │
│  EVENT      │    │ PART_OF     │    │  ARTIFACT   │
└─────────────┘    └─────────────┘    └─────────────┘
```

**Graph Schema:**
- **Entities Table**: Named entities with types and confidence
- **Relationships Table**: Connections between entities
- **Occurrences Table**: Entity mentions in documents
- **Confidence Scores**: Reliability metrics for extraction

## Communication Patterns

### 1. Request-Response Pattern

Standard HTTP requests for stateless operations:
- Document upload and metadata retrieval
- History queries and statistics
- Configuration management

### 2. Streaming Pattern

Server-Sent Events for real-time data:
- Token-by-token answer generation
- Progress updates for long-running operations
- Live analytics and monitoring

```javascript
// Client-side SSE handling
const eventSource = new EventSource('/api/qa/ask');
eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    handleStreamingResponse(data);
};
```

### 3. Async Processing Pattern

Background processing for heavy operations:
- Document ingestion and entity extraction
- Batch vector embedding generation
- Large-scale data exports

## Security Architecture

### Authentication & Authorization (Future)

```
Security Flow:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│  API Key    │───▶│Authorization│
│             │    │Validation   │    │   Service   │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Session    │    │Rate Limiting│    │   Access    │
│ Management  │    │  Service    │    │  Control    │
└─────────────┘    └─────────────┘    └─────────────┘
```

**Security Features:**
- API key authentication
- Rate limiting per client
- Request validation and sanitization
- Secure file upload handling
- CORS configuration for web clients

### Data Privacy

- Local data processing (no external data transmission)
- Configurable data retention policies
- Secure file storage with access controls
- Audit logging for data access

## Scalability Considerations

### Horizontal Scaling

**Current Architecture:**
- Single-instance deployment with local storage
- In-memory caching for performance
- Local file system for document storage

**Future Scaling Options:**
- Database clustering with read replicas
- Distributed vector storage (Pinecone, Weaviate)
- Container orchestration (Kubernetes)
- Load balancing for API endpoints

### Performance Optimization

**Current Optimizations:**
- Singleton pattern for resource reuse
- Connection pooling for database access
- Async/await for I/O operations
- Streaming responses for large data

**Future Optimizations:**
- GPU acceleration for embeddings
- Distributed caching (Redis)
- Content Delivery Network (CDN) for static files
- Query optimization and indexing strategies

## Monitoring & Observability

### Logging Strategy

```python
# Structured logging with multiple levels
logger.info("Query processed", extra={
    "query_id": query_id,
    "response_time": elapsed_time,
    "sources_used": len(sources),
    "user_id": user_id
})
```

**Log Categories:**
- **Application Logs**: Business logic and user actions
- **Performance Logs**: Response times and resource usage
- **Error Logs**: Exceptions and failure scenarios
- **Audit Logs**: Security-related events

### Metrics Collection

**Current Metrics:**
- Query response times
- Document processing statistics
- Error rates and types
- Resource utilization

**Future Metrics:**
- User engagement analytics
- Model performance metrics
- System health indicators
- Business intelligence data

## Extension Points

### Plugin Architecture (Future)

```python
# Plugin interface for extensibility
class AnalysisPlugin:
    def analyze(self, text: str) -> Dict[str, Any]:
        raise NotImplementedError
    
    def get_metadata(self) -> Dict[str, str]:
        raise NotImplementedError

# Registration system
plugin_manager.register("sentiment", SentimentPlugin())
plugin_manager.register("topic", TopicModelingPlugin())
```

### Custom Model Integration

- Support for different LLM providers
- Custom embedding model configuration
- Pluggable entity extraction strategies
- Configurable retrieval algorithms

### API Extensions

- Custom endpoint registration
- Middleware for cross-cutting concerns
- Event system for decoupled components
- Webhook support for external integrations

## Technology Stack Summary

### Backend Technologies
- **Framework**: FastAPI 0.104+ with async support
- **Language**: Python 3.12.9
- **Database**: SQLite with sqlite-vec extension
- **Vector Search**: sentence-transformers embeddings
- **LLM Integration**: LangChain with OpenRouter
- **PDF Generation**: WeasyPrint with HTML fallback
- **Testing**: pytest with async support

### Development Tools
- **Environment**: Conda/pip with virtual environments
- **Code Quality**: black, isort, flake8, mypy
- **Documentation**: Markdown with comprehensive guides
- **Version Control**: Git with conventional commits

### Deployment Options
- **Development**: Local uvicorn server
- **Production**: Docker containers (future)
- **Scaling**: Kubernetes orchestration (future)
- **Monitoring**: Structured logging with external tools

## Design Principles

### 1. Modularity
- Clear separation of concerns
- Minimal coupling between components
- Well-defined interfaces and contracts

### 2. Scalability
- Async processing for I/O operations
- Stateless design where possible
- Horizontal scaling readiness

### 3. Reliability
- Comprehensive error handling
- Graceful degradation strategies
- Retry mechanisms for transient failures

### 4. Performance
- Caching at multiple levels
- Streaming for large responses
- Efficient data structures and algorithms

### 5. Maintainability
- Consistent coding standards
- Comprehensive testing coverage
- Clear documentation and examples

This architecture provides a solid foundation for the current Phase 5 implementation while maintaining flexibility for future enhancements and scaling requirements.
