# SocioRAG Logging System

## Overview

SocioRAG uses a consolidated logging system that organizes application logs into a few structured files instead of many separate files. This makes log management easier and reduces clutter.

## Log Files

The system uses the following main log files:

| File | Purpose | Format | Retention |
|------|---------|--------|-----------|
| `sociorag_application.log` | Combined application output from both frontend and backend processes | Plain text | 10 recent files |
| `sociorag.log` | Application logs with main events | Formatted text | 5 recent files |
| `sociorag_errors.log` | Error-only logs for troubleshooting | Detailed text | 3 recent files |
| `sociorag_structured.log` | Structured JSON logs for automated analysis | JSON | 3 recent files |
| `app_manager.log` | Process management logs | Plain text | Not rotated |

## Consolidated Logging

The consolidated logging approach has several benefits:
- Fewer log files to manage
- Consistent log format
- Better log retention management
- Reduced disk space usage
- Simplified troubleshooting

### PowerShell Redirection Approach

To maintain a single application log while working within PowerShell's limitations (which doesn't allow redirecting both stdout and stderr to the same file), we:

1. Use a temporary file for stderr
2. Implement background jobs to merge logs in real-time
3. Clean up temporary files during shutdown

For more details, see `docs/powershell_redirection_fix.md`.

## Log Management

### Viewing Logs

```powershell
# View the main application log
Get-Content -Path "logs\sociorag_application.log" -Tail 50

# View only error logs
Get-Content -Path "logs\sociorag_errors.log"

# View process management logs
Get-Content -Path "logs\app_manager.log"
```

### Cleaning Up Logs

You can clean up log files using the provided script:

```powershell
# Run the cleanup script
.\clean_logs.ps1
```

Or directly using the app manager:

```powershell
.\scripts\production\app_manager.ps1 -Action clean
```

## Log Analysis

The system provides API endpoints for advanced log analysis:

- `/api/logs/health` - System health status
- `/api/logs/errors` - Error summary
- `/api/logs/performance` - Performance metrics
- `/api/logs/search` - Search through logs
- `/api/logs/stats` - Log statistics

For more information, see the [Logging System Documentation](../docs/logging_system_documentation.md).
