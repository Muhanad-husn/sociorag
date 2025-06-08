# PowerShell Redirection Fix

This document describes the fix implemented to resolve the PowerShell redirection issue in SocioRAG's production scripts.

## Problem

When starting the SocioRAG application using the production scripts, the following error was encountered:

```
This command cannot be run because "RedirectStandardOutput" and "RedirectStandardError" are same. 
Give different inputs and Run your command again.
```

This error occurs because PowerShell does not allow redirecting both standard output and standard error to the same file directly. This was causing startup failures in the `app_manager.ps1` script.

## Solution

The issue was resolved by implementing a workaround that:

1. Redirects standard output to the main log file directly
2. Redirects standard error to a temporary unique log file
3. Creates a background job that continuously monitors the temporary error log file
4. Merges content from the error log into the main log file
5. Cleans up temporary log files when the application stops

This approach allows us to maintain the benefits of consolidated logging while working within PowerShell's limitations.

## Implementation Details

### Changes to app_manager.ps1

1. **Modified Process Start Logic**:
   - Created a unique temporary error log for each process
   - Implemented background job for real-time log merging
   - Added cleanup when stopping services

2. **Enhanced Log Cleanup**:
   - Added temporary log files to cleanup patterns
   - Implemented temporary log merging during shutdown
   - Added background job cleanup

### Benefits

- **Consolidated Logs**: Still maintains a single application log file
- **No Lost Output**: Captures all stdout and stderr output
- **Reliability**: Prevents startup failures
- **Clean Shutdown**: Properly cleans up temporary files

## Future Improvements

In the future, we could consider:

1. Using a PowerShell wrapper function to handle redirection more elegantly
2. Implementing a dedicated log monitoring process rather than background jobs
3. Adding log rotation to the application log file

## References

- [PowerShell Start-Process Documentation](https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.management/start-process)
- [PowerShell Background Jobs](https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_jobs)
