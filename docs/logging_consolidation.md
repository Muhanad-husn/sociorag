# Consolidated Logging Implementation

This document describes the changes made to consolidate the SocioRAG logging system.

## Changes Made

1. **Consolidated Log Files**:
   - Reduced the number of log files from 10+ to 4 primary log files
   - Created a single `sociorag_application.log` file for both frontend and backend output
   - Removed separate debug log files
   - Increased size limits for remaining log files

2. **Fixed PowerShell Redirection Issue**:
   - Resolved the PowerShell limitation that prevents redirecting both stdout and stderr to the same file
   - Implemented a background job approach to monitor and merge temporary error logs
   - Added cleanup functionality to handle temporary log files during shutdown
   - Ensured all console output is properly captured and consolidated

3. **Enhanced Cleaning Functionality**:
   - Added a new `clean` action to the app_manager.ps1 script
   - Created a user-friendly `clean_logs.ps1` script for easy access
   - Implemented automatic log cleanup during application startup
   - Added log consolidation functionality to merge content from redundant logs

3. **Updated Documentation**:
   - Created a README.md file in the logs directory
   - Updated the logging_system_documentation.md file
   - Added informative messages in startup scripts

4. **Configuration Updates**:
   - Modified log rotation settings
   - Created a Python script to update .env file with consolidated settings
   - Standardized log file naming convention

## Benefits

- **Simplified Troubleshooting**: Fewer log files to check when diagnosing issues
- **Reduced Disk Space**: More efficient storage of log information
- **Better Organization**: Clear purpose for each log file
- **Improved Maintenance**: Automatic cleanup reduces clutter
- **Consistent Format**: Standardized logging approach across components

## How to Use

1. **View Application Output**:
   ```powershell
   Get-Content -Path "logs\sociorag_application.log" -Tail 50
   ```

2. **Clean Up Logs**:
   ```powershell
   .\clean_logs.ps1
   ```

3. **Start With Clean Logs**:
   ```powershell
   .\start_production.ps1 -CleanLogs
   ```

4. **View Only Errors**:
   ```powershell
   Get-Content -Path "logs\sociorag_errors.log"
   ```

## Log File Structure

| File | Purpose | Source |
|------|---------|--------|
| sociorag_application.log | Frontend/backend stdout/stderr | PowerShell redirection |
| sociorag.log | General application logs | Python logging |
| sociorag_errors.log | Error-only logs | Python logging |
| sociorag_structured.log | JSON structured logs | EnhancedLogger |
