# SocioRAG Production Deployment Guide

## Quick Production Start

### 🚀 Instant Launch (1-Command)
```powershell
# Start SocioRAG in production mode with monitoring
.\start_production.ps1
```

### ⚡ Essential Commands
```powershell
# Check status
.\scripts\production\app_manager.ps1 -Status

# Stop all services
.\stop_production.ps1

# View logs
Get-Content .\logs\sociorag.log -Tail 50 -Wait
```

### ✅ Access Points (Once Running)
- **Backend API**: http://127.0.0.1:8000
- **API Documentation**: http://127.0.0.1:8000/docs
- **Health Check**: http://127.0.0.1:8000/api/admin/health

## Comprehensive Production Deployment

### Prerequisites
- **Server**: Linux/Windows server
- **Resources**: Minimum 4GB RAM, 2 CPU cores, 20GB storage
- **Network**: Domain name and SSL certificates (optional)
- **API Key**: OpenRouter API key for LLM functionality

### Full Deployment Process

#### 1. Environment Setup
```bash
# Clone repository
git clone <your-repo> sociorag-prod
cd sociorag-prod

# Copy and configure environment
cp .env.example .env
```

#### 2. Configuration
```env
# .env
OPENROUTER_API_KEY=your_api_key_here
LOG_LEVEL=WARNING
ENV=production
GRAPH_DB_PATH=./data/graph.db
VECTOR_STORE_PATH=./vector_store
```

#### 3. Production Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/init_database_schema.py

# Start production server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Production Monitoring

### Health Monitoring
```bash
# Continuous health check
while true; do
  curl -s http://localhost:8000/api/admin/health || echo "Service down!"
  sleep 30
done
```

### Performance Monitoring
- **Response Times**: Monitor API response latencies
- **Memory Usage**: Track RAM consumption and garbage collection
- **CPU Usage**: Monitor processing load during peak usage
- **Disk Usage**: Track storage for documents and vector store

### Log Management
```bash
# View application logs
tail -f logs/sociorag.log

# View structured logs
tail -f logs/sociorag_structured.log

# View error logs
tail -f logs/sociorag_errors.log
```

## Security Configuration

### Firewall Rules
```bash
# Allow only necessary ports
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8000/tcp  # API (if not behind proxy)
ufw enable
```

### SSL/TLS Setup
```nginx
# Nginx configuration
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Environment Variables Security
```bash
# Secure environment file permissions
chmod 600 .env
chown app:app .env
```

## Backup and Disaster Recovery

### Automated Backups
```bash
#!/bin/bash
# backup_script.sh
BACKUP_DIR="/backups/sociorag/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup database
cp data/graph.db "$BACKUP_DIR/"
cp -r vector_store/ "$BACKUP_DIR/"

# Backup configuration
cp .env "$BACKUP_DIR/"
cp config.yaml "$BACKUP_DIR/"

# Archive and compress
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"
```

### Recovery Procedures
```bash
# Stop services (if using systemd)
sudo systemctl stop sociorag

# Restore from backup
tar -xzf backup_file.tar.gz
cp backup_data/* ./data/
cp backup_config/.env ./

# Restart services
sudo systemctl start sociorag
```

## Scaling and Performance

### Process Management
```bash
# Use PM2 for process management
npm install -g pm2

# Start with PM2
pm2 start "uvicorn backend.app.main:app --host 0.0.0.0 --port 8000" --name sociorag

# Scale to multiple instances
pm2 scale sociorag 4
```

### Load Balancing
```nginx
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
```

### Database Optimization
```sql
-- Optimize SQLite for production
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = memory;
```

## Troubleshooting

### Common Issues
1. **High Memory Usage**: Reduce context window and top-k parameters
2. **Slow Response Times**: Optimize database indices and consider caching
3. **API Rate Limits**: Implement request queuing and throttling
4. **Disk Space**: Set up log rotation and cleanup old vector data

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
uvicorn backend.app.main:app --reload --log-level debug
```

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
*This guide provides comprehensive production deployment instructions without containerization dependencies.*
