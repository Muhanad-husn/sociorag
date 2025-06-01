# SocioRAG Unified Production Deployment Guide

## Quick Production Start

### 🚀 Instant Launch (1-Command)
`powershell
# Start SocioRAG in production mode with monitoring
.\production_start.ps1
`

### ⚡ Essential Commands
`powershell
# Check status
.\production_status.ps1

# Start monitoring dashboard
.\monitoring_dashboard.ps1 -DetailedMode

# Run performance test
.\load_test.ps1 -ConcurrentUsers 3 -TestDurationMinutes 5

# Emergency stop
.\kill_app_processes.ps1
`

### ✅ Access Points (Once Running)
- **Backend API**: http://127.0.0.1:8000
- **API Documentation**: http://127.0.0.1:8000/docs
- **Health Check**: http://127.0.0.1:8000/api/admin/health

## Comprehensive Production Deployment

### Prerequisites
- **Server**: Linux/Windows with Docker support
- **Resources**: Minimum 4GB RAM, 2 CPU cores, 20GB storage
- **Network**: Domain name and SSL certificates (optional)
- **API Key**: OpenRouter API key for LLM functionality

### Full Deployment Process

#### 1. Environment Setup
`ash
# Clone repository
git clone <your-repo> sociorag-prod
cd sociorag-prod

# Copy and configure environment
cp .env.example .env.production
`

#### 2. Configuration
`nv
# .env.production
OPENROUTER_API_KEY=your_api_key_here
LOG_LEVEL=WARNING
ENV=production
GRAPH_DB_PATH=/app/data/graph.db
VECTOR_STORE_PATH=/app/data/vector_store
`

#### 3. Docker Deployment (Recommended)
`ash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# Verify deployment
curl http://your-domain.com/api/admin/health
`

#### 4. Manual Deployment
`ash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/init_databases.py

# Start production server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4
`

## Production Monitoring

### Health Monitoring
`ash
# Continuous health check
while true; do
  curl -s http://localhost:8000/api/admin/health || echo "Service down!"
  sleep 30
done
`

### Performance Monitoring
- **Response Times**: Monitor API response latencies
- **Memory Usage**: Track RAM consumption and garbage collection
- **CPU Usage**: Monitor processing load during peak usage
- **Disk Usage**: Track storage for documents and vector store

### Log Management
`ash
# View application logs
tail -f logs/sociorag.log

# View structured logs
tail -f logs/sociorag_structured.log

# View error logs
tail -f logs/sociorag_errors.log
`

## Security Configuration

### Firewall Rules
`ash
# Allow only necessary ports
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8000/tcp  # API (if not behind proxy)
ufw enable
`

### SSL/TLS Setup
`
ginx
# Nginx configuration
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \System.Management.Automation.Internal.Host.InternalHost;
        proxy_set_header X-Real-IP \;
    }
}
`

### Environment Variables Security
`ash
# Secure environment file permissions
chmod 600 .env.production
chown app:app .env.production
`

## Backup and Disaster Recovery

### Automated Backups
`ash
#!/bin/bash
# backup_script.sh
BACKUP_DIR="/backups/sociorag/"
mkdir -p ""

# Backup database
cp data/graph.db "/"
cp -r vector_store/ "/"

# Backup configuration
cp .env.production "/"
cp config.yaml "/"

# Archive and compress
tar -czf ".tar.gz" ""
rm -rf ""
`

### Recovery Procedures
`ash
# Stop services
docker-compose down

# Restore from backup
tar -xzf backup_file.tar.gz
cp backup_data/* ./data/
cp backup_config/.env.production ./

# Restart services
docker-compose up -d
`

## Scaling and Performance

### Horizontal Scaling
`yaml
# docker-compose.scale.yml
version: '3.8'
services:
  sociorag:
    image: sociorag:latest
    deploy:
      replicas: 3
    environment:
      - OPENROUTER_API_KEY=
`

### Load Balancing
`
ginx
upstream sociorag_backend {
    server localhost:8001;
    server localhost:8002;
    server localhost:8003;
}

server {
    location / {
        proxy_pass http://sociorag_backend;
    }
}
`

### Database Optimization
`python
# Optimize SQLite for production
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = memory;
`

## Troubleshooting

### Common Issues
1. **High Memory Usage**: Reduce context window and top-k parameters
2. **Slow Response Times**: Optimize database indices and consider caching
3. **API Rate Limits**: Implement request queuing and throttling
4. **Disk Space**: Set up log rotation and cleanup old vector data

### Debug Mode
`ash
# Enable debug logging
export LOG_LEVEL=DEBUG
uvicorn backend.app.main:app --reload --log-level debug
`

### Health Check Endpoints
- GET /api/admin/health - Overall system health
- GET /api/admin/metrics - Performance metrics
- GET /api/admin/config - Configuration status

## Production Readiness Checklist

**Pre-deployment:**
- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Firewall rules configured
- [ ] Backup procedures tested
- [ ] Monitoring systems active
- [ ] Load testing completed

**Post-deployment:**
- [ ] Health checks passing
- [ ] Performance within targets
- [ ] Monitoring alerts configured
- [ ] Backup schedule running
- [ ] Security audit completed
- [ ] Documentation updated

---
*This unified guide consolidates production deployment and runtime information for streamlined operations.*


---

# System Maintenance & Housekeeping

# SocioRAG Complete Housekeeping Guide

**Date:** May 27, 2025  
**Status:** Additional cleanup recommended  
**Previous Cleanup:** Phase 7 housekeeping completed (01:50 AM)

## Executive Summary

Your SocioRAG project has already undergone substantial housekeeping during Phase 7 completion, removing 6 superseded files and cleaning cache directories. However, several additional items remain that can be safely cleaned up to further optimize the workspace.

## Current Workspace Status

### ✅ Already Cleaned (Phase 7)
- **Superseded Test Files:** `e2e_test.py`, `final_e2e_test.py`, `test_phase5.py`
- **Development Utilities:** `debug_path.py`, `manual_test.py`  
- **Cache Directories:** Multiple `__pycache__` directories, `.pytest_cache`
- **SQLite Temp Files:** `graph.db-shm`, `graph.db-wal`

### 🧹 Additional Cleanup Opportunities

#### 1. Old Backup Directories (Large Impact)
- `phase4_backup_20250526_045633/` - Phase 4 backup from May 26
- `phase6_backup_cleanup_20250526_092007/` - Phase 6 cleanup backup from May 26
- **Impact:** Significant space savings, simplified workspace

#### 2. Superseded Configuration Files
- `environment.yml` - Conda environment file (superseded by `requirements.txt`)
- **Impact:** Eliminates confusion about which dependency file to use

#### 3. Remaining Development Utilities
- `fix_imports.py` - Import fixing utility (completed task)
- **Impact:** Removes completed development tools

#### 4. Cache Directories
- `LOCAL_APPDATA_FONTCONFIG_CACHE/` - Font configuration cache
- `.benchmarks/` - Benchmark cache directory
- **Impact:** Space savings and cleaner root directory

## Recommended Action Plan

### Step 1: Review Current State
Run the additional cleanup script in dry-run mode to see what would be cleaned:
```powershell
cd d:\sociorag
.\scripts\additional_cleanup.ps1 -DryRun
```

### Step 2: Execute Additional Cleanup
If the dry-run results look good, execute the actual cleanup:
```powershell
.\scripts\additional_cleanup.ps1
```

### Step 3: Validate System
After cleanup, verify system functionality:
```powershell
python final_e2e_test_working.py
```

## Expected Benefits

### 🎯 Workspace Organization
- **Cleaner Root Directory:** Remove old backup directories from workspace view
- **Simplified Structure:** Clear separation between production files and archives
- **Reduced Confusion:** Single source of truth for dependencies (`requirements.txt`)

### 💾 Space Recovery
- **Estimated Savings:** 500MB+ from old backups and caches
- **Performance:** Faster file operations with fewer directories to scan
- **IDE Performance:** Improved indexing with cleaner workspace

### 🚀 Production Readiness
- **Clear Dependencies:** Only `requirements.txt` for Python dependencies
- **Essential Files Only:** Remove completed development utilities
- **Deployment Clarity:** Obvious which files are needed for production

## Safety Measures

### ✅ Complete Backup Strategy
- All removed items backed up to timestamped directory
- Organized backup structure for easy restoration
- Detailed cleanup report generated

### ✅ Validation Process
- Pre-cleanup dry-run shows exactly what will be affected
- Post-cleanup validation ensures system functionality
- Easy rollback if issues occur

### ✅ Risk Assessment: 🟢 LOW
- Items identified are definitively superseded or cache files
- No production code or essential configuration affected
- Comprehensive backup ensures no data loss

## File Impact Summary

| Category | Items | Size Impact | Risk Level |
|----------|-------|-------------|------------|
| Old Backups | 2 directories | ~400MB+ | 🟢 None |
| Config Files | 1 file | ~1KB | 🟢 None |
| Dev Utilities | 1 file | ~2KB | 🟢 None |
| Cache Dirs | 2 directories | ~100MB+ | 🟢 None |
| **TOTAL** | **6 items** | **~500MB+** | **🟢 LOW** |

## Post-Cleanup Workspace Structure

After additional cleanup, your workspace will be optimally organized:

```
sociorag/
├── 📁 backend/              # Production backend
├── 📁 ui/                   # Production frontend  
├── 📁 docs/                 # Documentation
├── 📁 scripts/              # Deployment & utility scripts
├── 📁 tests/                # Test suites
├── 📁 vector_store/         # Vector database
├── 📁 data/                 # Graph database
├── 📁 input/                # Document inputs
├── 📁 saved/                # Saved outputs
├── 📁 cleanup_backups/      # All cleanup backups
├── 📄 final_e2e_test_working.py  # Main test suite
├── 📄 README.md             # Project guide
├── 📄 requirements.txt      # Python dependencies
├── 📄 config.yaml           # Configuration
├── 📄 APPLICATION_STATUS.md # Current status
├── 📄 STARTUP_GUIDE.md      # Startup instructions
└── 📄 quick_start.ps1       # Quick startup script
```

## Rollback Plan

If any issues occur after cleanup:

1. **Stop and Assess:** Identify the specific issue
2. **Restore from Backup:** Copy needed files from the timestamped backup directory
3. **Re-validate:** Run the test suite again
4. **Report:** Document what was restored and why

## Timeline

- **Analysis:** 2 minutes (dry-run review)
- **Cleanup Execution:** 3-5 minutes
- **Validation:** 2 minutes (test suite)
- **Total Time:** ~10 minutes

## Recommendation

✅ **PROCEED WITH ADDITIONAL CLEANUP**

**Reasoning:**
1. Phase 7 housekeeping was successful and well-documented
2. Remaining items are clearly superseded or cache files
3. Significant space and organization benefits
4. Low risk with comprehensive backup
5. Simple rollback available if needed

This additional cleanup will complete the workspace optimization started in Phase 7 and give you a perfectly organized, production-ready codebase.

---

**Next Action:** Run `.\scripts\additional_cleanup.ps1 -DryRun` to see the detailed cleanup plan.

