# SocioRAG Scripts Directory

This directory contains all PowerShell and batch scripts organized by purpose.

## Quick Start

**Production Use (Main Scripts):**
- Run `.\start_production.ps1` from the root directory to start SocioRAG
- Run `.\stop_production.ps1` from the root directory to stop SocioRAG

These are convenience wrappers that redirect to the organized scripts in `scripts\production\`.

## Directory Structure

### 📁 production/
Core production scripts for running SocioRAG:
- **start_production.ps1** - Main production startup script
- **stop_production.ps1** - Main production shutdown script  
- **app_manager.ps1** - Advanced application lifecycle management
- **PRODUCTION_QUICKSTART.md** - Production deployment documentation

### 📁 utilities/
Helper scripts for maintenance and troubleshooting:
- **kill_app_processes.ps1** - Force-kill all SocioRAG processes
- **clean_cache.ps1** - Clean all cache files and temporary data
- **production_status.ps1** - Check application status and health

### 📁 testing/
Performance testing and monitoring scripts:
- **load_test.ps1** - Load testing functionality
- **test_runner.ps1** - Test execution automation
- **performance_monitor.ps1** - Real-time performance monitoring
- **performance_test_monitor.ps1** - Testing-specific monitoring
- **monitoring_dashboard.ps1** - Performance dashboard

### 📁 archive/
Superseded or legacy scripts (kept for reference):
- **start_app.bat** - Original batch file (superseded by PowerShell)
- **production_start.ps1** - Duplicate production starter
- **quick_start.ps1** - Simple starter (superseded)
- **unified_start.ps1** - Complex unified starter (superseded)
- Various documentation consolidation scripts (one-time use)

## Usage Examples

### Starting SocioRAG for Production
```powershell
# From root directory (recommended)
.\start_production.ps1

# Or directly
.\scripts\production\start_production.ps1
```

### Stopping SocioRAG
```powershell
# From root directory (recommended)
.\stop_production.ps1

# Or directly
.\scripts\production\stop_production.ps1
```

### Force-kill if needed
```powershell
.\scripts\utilities\kill_app_processes.ps1
```

### Clean cache and temporary files
```powershell
.\scripts\utilities\clean_cache.ps1
```

### Check application status
```powershell
.\scripts\utilities\production_status.ps1
```

## Script Dependencies

The main production scripts are self-contained and require:
- PowerShell 5.1 or PowerShell 7+
- Python environment with SocioRAG dependencies
- Node.js for frontend (when applicable)

## Notes

- All scripts assume execution from the SocioRAG root directory
- Scripts are organized to avoid duplication and provide clear separation of concerns
- Archive directory contains legacy scripts maintained for historical reference
- Main production scripts (`start_production.ps1`, `stop_production.ps1`) are the primary entry points
