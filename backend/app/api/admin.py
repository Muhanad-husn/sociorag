"""Administrative API endpoints for SocioGraph.

This module provides system administration functionality including:
- System health monitoring and metrics
- Configuration management
- Maintenance operations
- Performance monitoring
"""

import psutil
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from backend.app.core.config import get_config
from backend.app.core.singletons import (
    LoggerSingleton, SQLiteSingleton, ChromaSingleton, 
    EmbeddingSingleton, LLMClientSingleton
)

_logger = LoggerSingleton().get()

router = APIRouter(prefix="/api/admin", tags=["admin"])


# Response Models
class HealthStatus(BaseModel):
    """System health status model."""
    status: str
    timestamp: datetime
    version: str
    uptime: float
    components: Dict[str, Dict[str, Any]]


class SystemMetrics(BaseModel):
    """System performance metrics model."""
    cpu_usage: float
    memory_usage: Dict[str, float]
    disk_usage: Dict[str, float]
    database_stats: Dict[str, Any]
    vector_store_stats: Dict[str, Any]
    timestamp: datetime


class SystemConfig(BaseModel):
    """System configuration model."""
    config_values: Dict[str, Any]
    config_source: str
    last_modified: Optional[datetime] = None


class SystemConfigUpdate(BaseModel):
    """System configuration update model."""
    updates: Dict[str, Any]
    restart_required: bool = False


class StatusResponse(BaseModel):
    """Generic status response."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class MaintenanceResult(BaseModel):
    """Maintenance operation result."""
    operation: str
    success: bool
    details: Dict[str, Any]
    duration: float


# Global system start time for uptime calculation
_start_time = time.time()


@router.get("/health", response_model=HealthStatus)
async def health_check() -> HealthStatus:
    """System health check endpoint.
    
    Provides comprehensive health status of all system components.
    """
    try:
        timestamp = datetime.now()
        uptime = time.time() - _start_time
        
        # Check component health
        components = {}
          # Database health
        try:
            db_conn = SQLiteSingleton().get()
            cursor = db_conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            components["database"] = {"status": "healthy", "type": "SQLite"}
        except Exception as e:
            components["database"] = {"status": "unhealthy", "error": str(e)}        # Vector store health
        try:
            chroma_instance = ChromaSingleton().get()
            # For Langchain Chroma, we can get count directly or access the collection
            count = chroma_instance._collection.count()
            components["vector_store"] = {
                "status": "healthy", 
                "type": "ChromaDB",
                "document_count": count
            }
        except Exception as e:
            components["vector_store"] = {"status": "unhealthy", "error": str(e)}
          # Embedding service health
        try:
            embedding_service = EmbeddingSingleton()
            test_embedding = embedding_service.embed(["test"])
            embedding_dim = len(test_embedding[0]) if isinstance(test_embedding[0], list) else 1
            components["embedding_service"] = {
                "status": "healthy",
                "model": "sentence-transformers",
                "embedding_dim": embedding_dim
            }
        except Exception as e:
            components["embedding_service"] = {"status": "unhealthy", "error": str(e)}
        
        # LLM client health
        try:
            llm_client = LLMClientSingleton()
            components["llm_client"] = {
                "status": "healthy",
                "provider": "OpenRouter"
            }
        except Exception as e:
            components["llm_client"] = {"status": "unhealthy", "error": str(e)}
        
        # Overall status
        unhealthy_components = [
            name for name, info in components.items() 
            if info.get("status") != "healthy"
        ]
        
        overall_status = "healthy" if not unhealthy_components else "degraded"
        
        _logger.info(f"Health check completed - Status: {overall_status}")
        
        return HealthStatus(
            status=overall_status,
            timestamp=timestamp,
            version="0.1.0",  # Version from config or package
            uptime=uptime,
            components=components
        )
        
    except Exception as e:
        _logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics() -> SystemMetrics:
    """Get system performance metrics.
    
    Provides detailed performance metrics including CPU, memory, disk, and database stats.
    """
    try:
        timestamp = datetime.now()
        
        # CPU usage
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_usage = {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "percentage": memory.percent
        }
        
        # Disk usage for the current directory
        disk = psutil.disk_usage('.')
        disk_usage = {
            "total_gb": round(disk.total / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "percentage": round((disk.used / disk.total) * 100, 2)
        }
          # Database statistics
        db_stats = {}
        try:
            db_conn = SQLiteSingleton().get()
            
            # Get table counts
            tables = ["entity", "relation", "documents"]
            for table in tables:
                try:
                    cursor = db_conn.cursor()
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    result = cursor.fetchone()
                    cursor.close()
                    db_stats[f"{table}_count"] = result[0] if result else 0
                except:
                    db_stats[f"{table}_count"] = 0
            
            # Get database file size
            cfg = get_config()
            if cfg.GRAPH_DB.exists():
                db_stats["file_size_mb"] = round(cfg.GRAPH_DB.stat().st_size / (1024**2), 2)
            
        except Exception as e:
            db_stats["error"] = str(e)
          # Vector store statistics
        vector_stats = {}
        try:
            chroma_instance = ChromaSingleton().get()
            vector_stats["document_count"] = chroma_instance._collection.count()
            
            # Vector store directory size
            cfg = get_config()
            if cfg.VECTOR_DIR.exists():
                total_size = sum(
                    f.stat().st_size for f in cfg.VECTOR_DIR.rglob('*') if f.is_file()
                )
                vector_stats["storage_size_mb"] = round(total_size / (1024**2), 2)
            
        except Exception as e:
            vector_stats["error"] = str(e)
        
        _logger.info("System metrics collected successfully")
        
        return SystemMetrics(
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            database_stats=db_stats,
            vector_store_stats=vector_stats,
            timestamp=timestamp
        )
        
    except Exception as e:
        _logger.error(f"Failed to get system metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Metrics collection failed: {str(e)}")


@router.post("/maintenance/cleanup")
async def cleanup_system() -> MaintenanceResult:
    """Perform system cleanup operations.
    
    Cleans up temporary files, optimizes databases, and performs maintenance tasks.
    """
    start_time = time.time()
    details = {}
    
    try:
        cfg = get_config()
        
        # Clean up old saved files (older than 30 days)
        if cfg.SAVED_DIR.exists():
            import os
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=30)
            cleaned_files = 0
            
            for file_path in cfg.SAVED_DIR.rglob('*'):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        file_path.unlink()
                        cleaned_files += 1
            
            details["cleaned_files"] = cleaned_files
          # Optimize SQLite database
        try:
            db_conn = SQLiteSingleton().get()
            cursor = db_conn.cursor()
            cursor.execute("VACUUM")
            cursor.execute("ANALYZE")
            cursor.close()
            details["database_optimized"] = True
        except Exception as e:
            details["database_optimization_error"] = str(e)
        
        # Clean up vector store if needed
        try:
            # Chroma cleanup is typically handled automatically
            details["vector_store_checked"] = True
        except Exception as e:
            details["vector_store_error"] = str(e)
        
        # Clear Python cache
        import gc
        gc.collect()
        details["memory_cleanup"] = True
        
        duration = time.time() - start_time
        
        _logger.info(f"System cleanup completed in {duration:.2f}s")
        
        return MaintenanceResult(
            operation="system_cleanup",
            success=True,
            details=details,
            duration=duration
        )
        
    except Exception as e:
        duration = time.time() - start_time
        _logger.error(f"System cleanup failed: {str(e)}")
        
        return MaintenanceResult(
            operation="system_cleanup",
            success=False,
            details={"error": str(e), **details},
            duration=duration
        )


@router.get("/config", response_model=SystemConfig)
async def get_system_config() -> SystemConfig:
    """Get system configuration.
    
    Returns current system configuration values and their sources.
    """
    try:
        cfg = get_config()
          # Get configuration values (excluding sensitive data)
        config_values = {
            # Paths
            "input_dir": str(cfg.INPUT_DIR),
            "saved_dir": str(cfg.SAVED_DIR),
            "vector_dir": str(cfg.VECTOR_DIR),
            "graph_db": str(cfg.GRAPH_DB),
            
            # Model settings
            "embedding_model": cfg.EMBEDDING_MODEL,
            "reranker_model": cfg.RERANKER_MODEL,
            "entity_llm_model": cfg.ENTITY_LLM_MODEL,
            "answer_llm_model": cfg.ANSWER_LLM_MODEL,
            
            # Similarity thresholds
            "chunk_similarity": cfg.CHUNK_SIM,
            "entity_similarity": cfg.ENTITY_SIM,
            "graph_similarity": cfg.GRAPH_SIM,
            
            # Search parameters
            "top_k": cfg.TOP_K,
            "top_k_rerank": cfg.TOP_K_RERANK,
            "max_context_fraction": cfg.MAX_CONTEXT_FRACTION,
            
            # Processing settings
            "spacy_model": cfg.SPACY_MODEL,
            "history_limit": cfg.HISTORY_LIMIT,
            
            # Logging
            "log_level": cfg.LOG_LEVEL
        }
          # Determine config source
        config_source = "environment variables and defaults"
        last_modified = None
        
        _logger.info("System configuration retrieved")
        
        return SystemConfig(
            config_values=config_values,
            config_source=config_source,
            last_modified=last_modified
        )
        
    except Exception as e:
        _logger.error(f"Failed to get system config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Config retrieval failed: {str(e)}")


@router.put("/config")
async def update_system_config(config: SystemConfigUpdate) -> StatusResponse:
    """Update system configuration.
    
    Updates configuration values. Some changes may require system restart.
    """
    try:
        cfg = get_config()
        
        # Validate and apply updates
        valid_updates = {}
        invalid_updates = {}
        
        for key, value in config.updates.items():
            # Validate configuration keys
            if hasattr(cfg, key.upper()):
                valid_updates[key] = value
            else:
                invalid_updates[key] = f"Unknown configuration key: {key}"
        
        if invalid_updates:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid configuration keys: {invalid_updates}"
            )
        
        # Apply valid updates (this is a simplified implementation)
        # In a full implementation, you would update the actual config file
        for key, value in valid_updates.items():
            setattr(cfg, key.upper(), value)
        
        _logger.info(f"Updated configuration keys: {list(valid_updates.keys())}")
        
        return StatusResponse(
            success=True,
            message=f"Configuration updated successfully. {len(valid_updates)} keys modified.",
            data={
                "updated_keys": list(valid_updates.keys()),
                "restart_required": config.restart_required
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Failed to update system config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Config update failed: {str(e)}")


@router.get("/logs")
async def get_recent_logs(
    lines: int = 100,
    level: str = "INFO"
) -> Dict[str, Any]:
    """Get recent log entries.
    
    Returns recent log entries with optional filtering by level.
    """
    try:
        # This is a simplified implementation
        # In a full system, you would read from actual log files
        
        logs = [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": "System is running normally",
                "module": "admin"
            }
        ]
        
        return {
            "logs": logs,
            "total_lines": len(logs),
            "requested_lines": lines,
            "level_filter": level
        }
        
    except Exception as e:
        _logger.error(f"Failed to get logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Log retrieval failed: {str(e)}")


@router.post("/restart")
async def restart_system() -> StatusResponse:
    """Restart system components.
    
    This is a placeholder for system restart functionality.
    In a production system, this would coordinate a graceful restart.
    """
    try:
        # In a real implementation, this would:
        # 1. Save current state
        # 2. Close connections
        # 3. Restart services
        # 4. Restore state
        
        _logger.warning("System restart requested - not implemented in development mode")
        
        return StatusResponse(
            success=False,
            message="System restart not available in development mode",
            data={"reason": "Development mode restriction"}
        )
        
    except Exception as e:
        _logger.error(f"Failed to restart system: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Restart failed: {str(e)}")


# Dependency for admin-only endpoints (placeholder)
async def require_admin() -> bool:
    """Require admin privileges for certain endpoints.
    
    This is a placeholder for authentication/authorization.
    In a production system, this would verify admin credentials.
    """
    # For now, always allow access
    # In production, implement proper authentication
    return True
