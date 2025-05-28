# Enhanced Logging System Documentation

The SocioRAG application features a comprehensive, production-ready logging system with advanced monitoring, analysis, and debugging capabilities. This documentation provides a complete overview of the logging architecture, configuration options, and usage patterns.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Core Components](#core-components)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Log Analysis](#log-analysis)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The enhanced logging system provides:

- **Structured JSON Logging**: Machine-readable log entries with consistent formatting
- **Correlation IDs**: Track requests across multiple components and services
- **Performance Monitoring**: Automatic timing and performance metrics collection
- **Real-time Analysis**: Live log analysis with error summaries and performance insights
- **REST API**: Complete API for log analysis, search, and monitoring
- **Automatic Cleanup**: Configurable log rotation and retention policies
- **Health Monitoring**: System health checks and alerting capabilities

## Architecture

### Core Components

```
Enhanced Logging System
├── LoggerSingleton          # Traditional logging singleton
├── EnhancedLogger          # Advanced logging with correlation IDs
├── LoggingMiddleware       # FastAPI request/response logging
├── LogAnalyzer            # Log analysis and monitoring
└── Logs API Router        # REST API endpoints
```

### Log Files

The system generates multiple log files in the `logs/` directory:

- `sociorag_main.log` - Main application logs (rotated at 10MB)
- `sociorag_debug.log` - Debug-level logs (rotated at 10MB)
- `sociorag_error.log` - Error-only logs (rotated at 5MB)
- `sociorag_startup.log` - Application startup logs
- `sociorag_structured.log` - Structured JSON logs with correlation IDs

## Configuration

### Environment Variables

Configure the logging system using these environment variables in your `.env` file:

```bash
# Basic Logging
LOG_LEVEL=INFO

# Enhanced Logging Features
ENHANCED_LOGGING_ENABLED=true
LOG_STRUCTURED_FORMAT=true
LOG_CORRELATION_ENABLED=true
LOG_PERFORMANCE_TRACKING=true

# File Management
LOG_FILE_RETENTION_DAYS=30
LOG_MAX_FILE_SIZE_MB=100
LOG_CLEANUP_INTERVAL_HOURS=24

# Performance Monitoring
LOG_SLOW_REQUEST_THRESHOLD_MS=1000
LOG_ERROR_RATE_THRESHOLD=0.05
LOG_PERFORMANCE_SAMPLE_RATE=1.0

# Health Monitoring
LOG_HEALTH_CHECK_INTERVAL_MINUTES=15
LOG_ALERT_ERROR_THRESHOLD=10
LOG_ALERT_PERFORMANCE_THRESHOLD_MS=2000
```

### Configuration Options

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `ENHANCED_LOGGING_ENABLED` | bool | `true` | Enable enhanced logging features |
| `LOG_STRUCTURED_FORMAT` | bool | `true` | Use JSON structured logging |
| `LOG_CORRELATION_ENABLED` | bool | `true` | Enable correlation ID tracking |
| `LOG_PERFORMANCE_TRACKING` | bool | `true` | Track operation performance |
| `LOG_FILE_RETENTION_DAYS` | int | `30` | Days to retain log files |
| `LOG_MAX_FILE_SIZE_MB` | int | `100` | Maximum size before rotation |
| `LOG_CLEANUP_INTERVAL_HOURS` | int | `24` | Hours between cleanup runs |
| `LOG_SLOW_REQUEST_THRESHOLD_MS` | int | `1000` | Threshold for slow requests |
| `LOG_ERROR_RATE_THRESHOLD` | float | `0.05` | Error rate alert threshold |
| `LOG_PERFORMANCE_SAMPLE_RATE` | float | `1.0` | Performance sampling rate |

## Core Components

### EnhancedLogger

The `EnhancedLogger` class provides advanced logging capabilities:

```python
from backend.app.core.enhanced_logger import EnhancedLogger

# Initialize the enhanced logger
enhanced_logger = EnhancedLogger()

# Use correlation context
with enhanced_logger.correlation_context("operation-123"):
    enhanced_logger.info("Processing request", extra={"user_id": "user123"})
    
# Performance timing decorator
@enhanced_logger.time_operation("database_query")
async def query_database():
    # Your database query here
    pass

# Manual performance tracking
with enhanced_logger.track_performance("custom_operation"):
    # Your code here
    pass
```

### LoggingMiddleware

Automatic request/response logging for FastAPI:

```python
from backend.app.core.logging_middleware import LoggingMiddleware
from fastapi import FastAPI

app = FastAPI()
app.add_middleware(LoggingMiddleware)
```

The middleware automatically:
- Assigns correlation IDs to requests
- Logs request/response details
- Tracks API performance
- Handles error logging

### LogAnalyzer

Comprehensive log analysis capabilities:

```python
from backend.app.core.log_analyzer import LogAnalyzer

analyzer = LogAnalyzer()

# Get error summary
errors = await analyzer.get_error_summary(hours=24)

# Performance metrics
metrics = await analyzer.get_performance_metrics(hours=1)

# System health check
health = await analyzer.get_system_health()

# Search logs
results = await analyzer.search_logs(
    query="error", 
    start_time=datetime.now() - timedelta(hours=1)
)
```

## API Endpoints

The logging system exposes REST API endpoints for monitoring and analysis:

### Error Analysis

```bash
# Get error summary for last 24 hours
GET /api/logs/errors?hours=24

# Response:
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
  "error_trend": {...}
}
```

### Performance Metrics

```bash
# Get performance metrics for last hour
GET /api/logs/performance?hours=1

# Response:
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

### System Health

```bash
# Get current system health
GET /api/logs/health

# Response:
{
  "status": "healthy",
  "error_rate": 0.01,
  "avg_response_time": 234.5,
  "active_users": 12,
  "last_error": "2024-01-15T12:00:00Z",
  "uptime_hours": 168.5,
  "log_file_sizes": {...}
}
```

### Log Search

```bash
# Search logs with filters
POST /api/logs/search
{
  "query": "database error",
  "level": "ERROR",
  "start_time": "2024-01-15T00:00:00Z",
  "end_time": "2024-01-15T23:59:59Z",
  "limit": 100
}
```

### Correlation Tracing

```bash
# Trace all logs for a correlation ID
GET /api/logs/correlation/{correlation_id}

# Response: Array of all log entries with the same correlation ID
```

### Administrative Operations

```bash
# Cleanup old log files
POST /api/logs/cleanup

# Get log statistics
GET /api/logs/stats

# Response:
{
  "total_entries": 15420,
  "file_count": 5,
  "total_size_mb": 12.8,
  "oldest_entry": "2024-01-01T00:00:00Z",
  "newest_entry": "2024-01-15T15:30:00Z",
  "entries_by_level": {...}
}
```

## Usage Examples

### Basic Logging

```python
from backend.app.core.enhanced_logger import EnhancedLogger

logger = EnhancedLogger()

# Structured logging with context
logger.info("User logged in", extra={
    "user_id": "user123",
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0..."
})

# Error logging with details
try:
    result = risky_operation()
except Exception as e:
    logger.error("Operation failed", extra={
        "operation": "data_processing",
        "error_type": type(e).__name__,
        "error_details": str(e)
    })
```

### Correlation Tracking

```python
# Web request handler
async def process_request(request_id: str):
    with logger.correlation_context(request_id):
        logger.info("Starting request processing")
        
        # All subsequent logs will include the correlation ID
        await process_data()
        await save_results()
        
        logger.info("Request completed successfully")

# The correlation ID flows through all operations
async def process_data():
    logger.debug("Processing data")  # Includes correlation ID
    
async def save_results():
    logger.info("Saving results")   # Includes correlation ID
```

### Performance Monitoring

```python
# Method decorator
@logger.time_operation("user_authentication")
async def authenticate_user(credentials):
    # Authentication logic
    return user

# Context manager
async def complex_operation():
    with logger.track_performance("data_analysis"):
        # CPU-intensive operation
        results = analyze_large_dataset()
        
    # Performance metrics automatically logged
    return results
```

### Error Analysis

```python
from backend.app.core.log_analyzer import LogAnalyzer

analyzer = LogAnalyzer()

# Daily error report
async def generate_error_report():
    errors = await analyzer.get_error_summary(hours=24)
    
    if errors['error_rate'] > 0.05:  # 5% error rate
        # Send alert
        await send_alert(f"High error rate: {errors['error_rate']:.2%}")
    
    return errors

# Performance monitoring
async def check_performance():
    metrics = await analyzer.get_performance_metrics(hours=1)
    
    slow_endpoints = [
        ep for ep in metrics['endpoints'] 
        if ep['avg_time'] > 1000  # 1 second
    ]
    
    if slow_endpoints:
        await send_performance_alert(slow_endpoints)
```

## Log Analysis

### Structured Log Format

Enhanced logs use JSON format for machine readability:

```json
{
  "timestamp": "2024-01-15T15:30:45.123Z",
  "level": "INFO",
  "logger": "sociorag.api",
  "message": "Request processed successfully",
  "correlation_id": "req_abc123def456",
  "request_id": "api_789xyz",
  "user_id": "user123",
  "endpoint": "/api/qa/ask",
  "method": "POST",
  "status_code": 200,
  "response_time_ms": 245.7,
  "extra": {
    "question_length": 128,
    "answer_length": 1024,
    "sources_count": 3
  }
}
```

### Performance Metrics

Performance data is automatically collected and includes:

- **Request timing**: Total response time, processing time
- **Resource usage**: Memory, CPU utilization
- **Database metrics**: Query time, connection pool status
- **Cache performance**: Hit rates, miss rates
- **Error rates**: By endpoint, by time period

### Health Monitoring

The system continuously monitors:

- **Error rates**: Overall and by endpoint
- **Response times**: Averages and percentiles
- **Active users**: Concurrent user tracking
- **System resources**: Disk space, memory usage
- **Log file sizes**: Automatic rotation triggers

## Best Practices

### Logging Guidelines

1. **Use Structured Data**: Include relevant context in the `extra` parameter
2. **Correlation IDs**: Always use correlation context for request flows
3. **Appropriate Levels**: Use INFO for business events, DEBUG for technical details
4. **Performance Sensitive**: Use decorators for automatic timing
5. **Error Context**: Include operation details in error logs

### Performance Considerations

1. **Sampling**: Use `LOG_PERFORMANCE_SAMPLE_RATE` to reduce overhead
2. **Async Operations**: Use async log analysis methods
3. **Batch Processing**: Group log analysis operations when possible
4. **Cleanup**: Regular cleanup prevents disk space issues

### Security Considerations

1. **Sensitive Data**: Never log passwords, tokens, or personal data
2. **IP Addresses**: Consider privacy implications
3. **Log Access**: Restrict access to log files and API endpoints
4. **Retention**: Follow data retention policies

## Troubleshooting

### Common Issues

#### High Disk Usage
```bash
# Check log file sizes
curl http://localhost:8000/api/logs/stats

# Cleanup old files
curl -X POST http://localhost:8000/api/logs/cleanup
```

#### Missing Correlation IDs
```python
# Ensure correlation context is used
with logger.correlation_context("operation-id"):
    # Your code here
    pass
```

#### Performance Impact
```bash
# Reduce sampling rate
LOG_PERFORMANCE_SAMPLE_RATE=0.1  # 10% sampling
```

#### Log Analysis Errors
```python
# Check log file permissions
# Verify log file format
# Check disk space
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
LOG_LEVEL=DEBUG
```

This provides detailed information about:
- Log processing operations
- File I/O operations
- Performance measurement overhead
- Correlation ID propagation

### Monitoring Alerts

Set up monitoring for:
- High error rates (`LOG_ERROR_RATE_THRESHOLD`)
- Slow responses (`LOG_SLOW_REQUEST_THRESHOLD_MS`)
- Disk space usage
- Log processing errors

## API Reference

For complete API documentation, visit the interactive Swagger UI at:
`http://localhost:8000/docs#/logs`

The logs API provides comprehensive endpoints for:
- Error analysis and summaries
- Performance monitoring and metrics
- User activity tracking
- System health monitoring
- Log search and filtering
- Correlation tracing
- Administrative operations
- Statistics and reporting

## Integration Examples

### FastAPI Application

```python
from fastapi import FastAPI
from backend.app.core.logging_middleware import LoggingMiddleware
from backend.app.core.enhanced_logger import EnhancedLogger

app = FastAPI()
app.add_middleware(LoggingMiddleware)

logger = EnhancedLogger()

@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    with logger.correlation_context(f"get_user_{user_id}"):
        logger.info("Retrieving user", extra={"user_id": user_id})
        
        try:
            user = await fetch_user(user_id)
            logger.info("User retrieved successfully", 
                       extra={"user_id": user_id, "found": True})
            return user
        except UserNotFound:
            logger.warning("User not found", 
                          extra={"user_id": user_id, "found": False})
            raise HTTPException(404, "User not found")
```

### Background Tasks

```python
from celery import Celery
from backend.app.core.enhanced_logger import EnhancedLogger

app = Celery('sociorag')
logger = EnhancedLogger()

@app.task
@logger.time_operation("document_processing")
def process_document(doc_id: str):
    with logger.correlation_context(f"process_doc_{doc_id}"):
        logger.info("Starting document processing", 
                   extra={"document_id": doc_id})
        
        # Processing logic
        result = heavy_processing(doc_id)
        
        logger.info("Document processing completed",
                   extra={"document_id": doc_id, "result_size": len(result)})
        
        return result
```

This enhanced logging system provides comprehensive monitoring, debugging, and analysis capabilities for the SocioRAG application, enabling effective production operation and maintenance.
