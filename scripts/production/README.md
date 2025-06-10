# SocioRAG Production Scripts

This directory contains scripts for managing the SocioRAG application in a production environment.

## 📋 Available Scripts

| Script | Description |
|--------|-------------|
| `app_manager.ps1` | Main script for starting, stopping, and checking status of SocioRAG services |
| `PRODUCTION_QUICKSTART.md` | Quick reference guide for production operations |

## 📝 Usage Examples

### Starting the Application

```powershell
# Start the application (basic)
.\scripts\production\app_manager.ps1 -Action start

# Start with monitoring dashboard
.\scripts\production\app_manager.ps1 -Action start -EnableMonitoring

# Start and wait for services to be ready before returning
.\scripts\production\app_manager.ps1 -Action start -WaitForReady

# Start with all options
.\scripts\production\app_manager.ps1 -Action start -EnableMonitoring -WaitForReady -TimeoutSeconds 120
```

### Managing the Application

```powershell
# Check application status
.\scripts\production\app_manager.ps1 -Action status

# Stop the application
.\scripts\production\app_manager.ps1 -Action stop

# Restart the application
.\scripts\production\app_manager.ps1 -Action restart
```

## 🔧 Parameters for app_manager.ps1

| Parameter | Type | Description |
|-----------|------|-------------|
| `-Action` | String | Required. Action to perform: "start", "stop", "restart", or "status" |
| `-WaitForReady` | Switch | Optional. Wait until services are healthy before returning |
| `-SkipBrowser` | Switch | Optional. Don't open browser when starting services |
| `-EnableMonitoring` | Switch | Optional. Start the monitoring dashboard when starting services |
| `-TimeoutSeconds` | Integer | Optional. Timeout in seconds when waiting for services (default: 60) |

## 🚨 Troubleshooting

If you encounter issues with the application not starting properly:

1. Check the logs directory for error messages
2. Ensure all required dependencies are installed
3. Verify that ports 8000 (backend) and 5173 (frontend) are available
4. Try stopping the application and starting it again

For detailed monitoring and debugging, use the monitoring scripts in the `../testing/` directory.

## 📝 Simplified Usage

For convenience, you can also use these scripts from the project root:

```powershell
# Start the application with default settings
.\start.ps1

# Start with monitoring enabled
.\start.ps1 -EnableMonitoring

# Stop the application
.\stop.ps1
```
