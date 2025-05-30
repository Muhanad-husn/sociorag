# SocioRAG Project Overview

## Project Summary

SocioRAG is a comprehensive system for analyzing and visualizing social dynamics in texts through advanced NLP, entity extraction, vector search, and answer generation capabilities. The system follows a modular architecture with distinct phases for data ingestion, storage, retrieval, and answer generation.

## Current Status: Production Ready

The project is now production-ready with all major development phases completed. The codebase has been streamlined by removing E2E tests and non-essential files to focus on the core functionality. The application is now more maintainable and easier to deploy.

## Architecture Overview

### Core Components

1. **Data Ingestion Pipeline** (`backend/app/ingest/`)
   - Enhanced entity extraction with LLM-powered analysis
   - Robust JSON parsing with multiple fallback strategies
   - Batch processing with retry mechanisms
   - Document chunking and metadata extraction

2. **Vector Storage & Retrieval** (`backend/app/retriever/`)
   - SQLite-vec based vector storage (migrated from SQLite-vss)
   - Semantic search with reranking
   - Context retrieval with relevance scoring
   - Efficient similarity matching

3. **Answer Generation** (`backend/app/answer/`)
   - Complete response generation with LLM integration
   - Citation management and source linking
   - PDF export with Playwright for enhanced performance
   - Query history tracking with analytics

4. **Core Infrastructure** (`backend/app/core/`)
   - Singleton pattern for shared resources
   - Centralized configuration management
   - Logging and error handling
   - Database connections

5. **API Layer** (`backend/app/api/`)
   - FastAPI endpoints for Q&A functionality
   - Standard HTTP request/response architecture
   - File upload and static serving
   - RESTful interface design

## Technology Stack

### Backend
- **Framework**: FastAPI with async/await support
- **LLM Integration**: LangChain with OpenRouter API
- **Vector Database**: SQLite-vec for similarity search
- **Graph Database**: SQLite for entity relationships
- **Entity Extraction**: spaCy + Custom LLM pipeline
- **PDF Generation**: Playwright with browser automation
- **Architecture**: Request/Response with JSON APIs

### Dependencies
- **Core**: Python 3.12.9, FastAPI, LangChain, Pydantic
- **ML/NLP**: spaCy, sentence-transformers, sqlite-vec
- **PDF**: Playwright, Jinja2 templates
- **Utilities**: python-multipart, aiofiles

### Development Tools
- **Environment**: Conda/pip with virtual environments
- **Testing**: Pytest with async support
- **Documentation**: Markdown with comprehensive guides
- **Configuration**: YAML/ENV based centralized config

## Key Features

### 1. Enhanced Entity Extraction
- LLM-powered entity and relationship extraction
- Multiple JSON parsing strategies with fallbacks
- Retry mechanisms for API reliability
- Response caching for performance optimization
- Batch processing with concurrency control

### 2. Advanced Vector Retrieval
- Semantic similarity search with embeddings
- Context retrieval with relevance scoring
- Reranking for improved result quality
- Configurable similarity thresholds
- Efficient storage with SQLite-vec

### 3. Complete Answer Generation
- Comprehensive response generation with LLM integration
- Citation management with numbered references
- Context-aware prompt construction
- Standard JSON response format
- Comprehensive error handling

### 4. PDF Export System
- Professional PDF generation with Playwright
- Custom CSS styling and layout
- HTML fallback for dependency issues
- Static file serving through FastAPI
- Download management

### 5. Query History & Analytics
- JSONL-based append-only logging
- Query statistics and performance metrics
- History retrieval with pagination
- Analytics for usage patterns
- Data persistence across sessions

## Phase Implementation Status

### ✅ Phase 1-4: Data Foundation
- Data ingestion pipeline with enhanced entity extraction
- Vector storage migration to SQLite-vec
- Graph database for entity relationships
- Retrieval system with reranking
- Core infrastructure and singletons

### ✅ Phase 5: Answer Generation & PDF Export
- Complete answer generation with citations
- PDF export with professional formatting
- Query history tracking and analytics
- FastAPI Q&A endpoints with SSE support
- Comprehensive testing and validation

### 🚧 Phase 6: FastAPI Back-End (Next)
- Complete API endpoint coverage
- Authentication and authorization
- Advanced file upload handling
- API documentation and testing
- Production deployment preparation

### 📋 Future Phases
- Frontend development (React/Vue/Angular)
- Real-time collaboration features
- Advanced analytics and visualization
- Multi-language support
- Performance optimization

## Configuration Management

The project uses a centralized configuration system with multiple override options:

```python
from backend.app.core.config import get_config

# Default configuration
cfg = get_config()

# Custom configuration file
cfg = get_config("custom_config.yaml")

# Environment variable overrides via .env file
```

### Key Configuration Categories
- **Paths**: Directory structure and file locations
- **Models**: LLM and embedding model specifications
- **Thresholds**: Similarity and relevance thresholds
- **Limits**: Performance and storage limits
- **Resources**: External dependencies and models

## Error Handling & Reliability

### Robust Error Management
- Comprehensive exception handling throughout
- Graceful degradation for missing dependencies
- Detailed logging with configurable levels
- Fallback mechanisms for critical components
- User-friendly error messages

### Performance Considerations
- Async/await patterns for I/O operations
- Connection pooling and resource management
- Caching strategies for expensive operations
- Batch processing for bulk operations
- Memory-efficient response handling

## Testing & Validation

### Test Coverage
- Unit tests for individual components
- Integration tests for complete workflows
- Phase validation tests for milestone verification
- Example scripts for functionality demonstration
- Performance benchmarks for optimization

### Quality Assurance
- Comprehensive error testing
- Edge case handling validation
- Resource cleanup verification
- API endpoint testing
- PDF generation validation

## Development Workflow

### Setup Process
1. Environment creation (Conda recommended)
2. Dependency installation from requirements.txt
3. Configuration setup (.env and config.yaml)
4. Database initialization
5. Model download (spaCy, embeddings)

### Testing Workflow
1. Run phase validation tests
2. Execute integration tests
3. Validate API endpoints
4. Test PDF generation
5. Verify JSON responses

### Deployment Considerations
- Environment variable configuration
- Static file serving setup
- Database migration scripts
- Dependency management
- Performance monitoring

## Next Steps

### Immediate Actions (Phase 6)
1. Complete FastAPI endpoint coverage
2. Implement authentication system
3. Add comprehensive API documentation
4. Enhance error handling and validation
5. Prepare for production deployment

### Medium-term Goals
1. Frontend development initiation
2. Real-time collaboration features
3. Advanced analytics implementation
4. Performance optimization
5. Multi-language support

### Long-term Vision
1. Production deployment and scaling
2. Advanced visualization capabilities
3. Machine learning model improvements
4. Community features and sharing
5. Commercial deployment options

## Documentation Resources

- **Implementation Guides**: Detailed phase implementation summaries
- **API Documentation**: Endpoint specifications and examples
- **Configuration Guide**: Setup and customization instructions
- **Testing Guide**: Test execution and validation procedures
- **Troubleshooting**: Common issues and solutions

The SocioRAG project represents a comprehensive solution for text analysis and social dynamics visualization, with a solid foundation for future enhancements and scalability.
