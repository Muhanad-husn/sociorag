# SocioRAG Logging and Monitoring Guide

This guide explains how to use the enhanced logging and monitoring features of SocioRAG.

## Overview

SocioRAG now includes comprehensive logging and monitoring capabilities to help you track application behavior, debug issues, and monitor performance in real-time.

### Log Files

The application creates several log files in the `logs/` directory:

- **`sociorag.log`** - Main application log with INFO level and above
- **`sociorag_debug.log`** - Detailed debug logs with DEBUG level and above  
- **`sociorag_errors.log`** - Error-only logs for quick issue identification

### Log Rotation

All log files use automatic rotation:
- Main and debug logs: 10MB max size, 5 backup files
- Error logs: 5MB max size, 3 backup files

## Starting the Application with Monitoring

### Enhanced Startup Script

Use the new `start_with_monitoring.ps1` script for better control:

```powershell
# Basic startup with monitoring
.\start_with_monitoring.ps1 -Monitor

# Show backend window (don't hide it)
.\start_with_monitoring.ps1 -ShowBackend

# Enable debug logging
.\start_with_monitoring.ps1 -DebugMode

# Monitor only errors
.\start_with_monitoring.ps1 -Monitor -ErrorsOnly

# Don't auto-open browser
.\start_with_monitoring.ps1 -NoAutoOpen

# Custom backend wait time (default 50 seconds)
.\start_with_monitoring.ps1 -BackendWait 60
```

### Parameters

- **`-Monitor`** - Start real-time log monitoring
- **`-ShowBackend`** - Keep backend window visible (useful for development)
- **`-DebugMode`** - Enable debug-level logging
- **`-ErrorsOnly`** - Monitor only error logs
- **`-NoAutoOpen`** - Don't automatically open browser
- **`-BackendWait`** - Seconds to wait for backend startup (default: 50)

## Real-Time Log Monitoring

### Monitor Logs Script

Use `monitor_logs.ps1` to view logs in real-time:

```powershell
# Monitor main application logs
.\monitor_logs.ps1 -Tail

# Monitor only errors
.\monitor_logs.ps1 -Errors -Tail

# Monitor debug logs
.\monitor_logs.ps1 -Debug -Tail

# Show recent logs without real-time monitoring
.\monitor_logs.ps1

# Show last 50 lines and then monitor
.\monitor_logs.ps1 -Tail -Lines 50
```

### Features

- **Color-coded output** - Errors in red, warnings in yellow, info in green
- **Auto-detection** - Waits for log files to be created
- **Multiple log types** - Main, error, and debug logs
- **Configurable history** - Show recent entries before monitoring

## Log Viewing and Analysis

### View Logs Script

Use `view_logs.ps1` to analyze logs after the fact:

```powershell
# View recent main logs
.\view_logs.ps1

# View error logs only
.\view_logs.ps1 -LogType errors

# View debug logs
.\view_logs.ps1 -LogType debug

# Show more lines
.\view_logs.ps1 -Lines 200

# Filter logs containing specific text
.\view_logs.ps1 -Filter "startup"

# Show logs since a specific time
.\view_logs.ps1 -Since "2024-05-27 10:00"

# Show log statistics
.\view_logs.ps1 -Stats

# Follow logs in real-time
.\view_logs.ps1 -Follow
```

### Advanced Filtering

```powershell
# Show all errors from today
.\view_logs.ps1 -LogType errors -Since "2024-05-27 00:00"

# Monitor specific component
.\view_logs.ps1 -Filter "retrieval" -Follow

# Get statistics for error logs
.\view_logs.ps1 -LogType errors -Stats
```

## Backend Performance Monitoring

### Startup Timing

The backend server requires **at least 50 seconds** to fully initialize. The enhanced startup script:

1. **Dependency Loading** (15-20 seconds) - ML models, NLP pipelines
2. **Database Initialization** (10-15 seconds) - SQLite, Chroma setup  
3. **Service Registration** (5-10 seconds) - API routes, middleware
4. **Health Check** (5-10 seconds) - Verification and readiness

### Performance Logs

Watch for these key startup events in logs:

```
INFO - Initializing SocioRAG FastAPI application...
INFO - EmbeddingSingleton: Loading sentence transformer model...
INFO - ChromaSingleton: Initializing vector store...
INFO - SQLiteSingleton: Connecting to graph database...
INFO - All API routers registered successfully
INFO - SocioRAG FastAPI application initialization complete
```

## Troubleshooting Common Issues

### Backend Startup Problems

1. **Check error logs first:**
   ```powershell
   .\view_logs.ps1 -LogType errors -Lines 50
   ```

2. **Monitor startup process:**
   ```powershell
   .\start_with_monitoring.ps1 -ShowBackend -DebugMode
   ```

3. **Common issues:**
   - Missing dependencies: Check for import errors
   - Port conflicts: Look for "Address already in use" errors
   - API key issues: Check for OpenRouter authentication errors

### Log File Issues

1. **Logs directory missing:**
   - Automatically created on first run
   - Check permissions if creation fails

2. **Log files not updating:**
   - Verify backend is running: `Get-Process | Where-Object {$_.ProcessName -like "*python*"}`
   - Check log level configuration

3. **Large log files:**
   - Automatic rotation prevents this
   - Manual cleanup: Remove old `*.log.*` files

## Development and Debugging

### Debug Mode

Enable debug logging for development:

```powershell
# Start with debug logging
.\start_with_monitoring.ps1 -DebugMode -ShowBackend

# Monitor debug logs
.\monitor_logs.ps1 -Debug -Tail
```

### Custom Log Levels

Set log level via environment variable:

```powershell
$env:LOG_LEVEL="DEBUG"
.\quick_start.ps1
```

Or in `.env` file:
```
LOG_LEVEL=DEBUG
```

### Performance Monitoring

Monitor key performance metrics:

```powershell
# Watch for performance-related logs
.\view_logs.ps1 -Filter "duration\|time\|seconds" -Follow

# Monitor retrieval pipeline
.\view_logs.ps1 -Filter "retrieval\|pipeline" -Follow
```

## Integration with Application

### Programmatic Access

Access logs from within the application:

```python
from backend.app.core.singletons import get_logger

logger = get_logger()
logger.info("Application event")
logger.warning("Potential issue detected")
logger.error("Error occurred", exc_info=True)
```

### Log Context

Add structured context to logs:

```python
logger.info(
    "Query processed successfully",
    extra={
        "query_id": query_id,
        "duration": processing_time,
        "chunk_count": len(chunks)
    }
)
```

## Best Practices

### Regular Monitoring

1. **During Development:**
   - Use `start_with_monitoring.ps1 -Monitor -DebugMode`
   - Keep error logs open: `monitor_logs.ps1 -Errors -Tail`

2. **Production Monitoring:**
   - Check error logs regularly: `view_logs.ps1 -LogType errors -Stats`
   - Monitor startup times and performance metrics

3. **Issue Investigation:**
   - Start with error logs: `view_logs.ps1 -LogType errors`
   - Use time-based filtering: `-Since "YYYY-MM-DD HH:MM"`
   - Follow debug logs for detailed analysis

### Log Management

1. **Regular Cleanup:**
   - Old rotated logs are automatically managed
   - Remove ancient backup files manually if needed

2. **Performance Impact:**
   - Debug logging has minimal performance impact
   - Reduce log level in production if needed

3. **Disk Space:**
   - Monitor logs directory size
   - Adjust rotation settings if needed

## Command Reference

### Quick Commands

```powershell
# Start with monitoring
.\start_with_monitoring.ps1 -Monitor

# Monitor errors only
.\monitor_logs.ps1 -Errors -Tail

# View recent errors
.\view_logs.ps1 -LogType errors

# Check log statistics
.\view_logs.ps1 -Stats

# Follow specific logs
.\view_logs.ps1 -Filter "your_filter" -Follow
```

### Advanced Usage

```powershell
# Custom startup configuration
.\start_with_monitoring.ps1 -DebugMode -ShowBackend -NoAutoOpen -BackendWait 60

# Time-based log analysis
.\view_logs.ps1 -Since "2024-05-27 09:00" -Filter "ERROR" -Lines 100

# Performance monitoring
.\view_logs.ps1 -Filter "duration\|performance" -Follow
```

This logging system provides comprehensive visibility into your SocioRAG application, making debugging and monitoring much easier than before.
