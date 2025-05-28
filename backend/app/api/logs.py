"""Log analysis and monitoring API endpoints.

This module provides endpoints for real-time log analysis, monitoring,
and system health checking using the enhanced logging system.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pydantic import BaseModel

from ..core.log_analyzer import LogAnalyzer
from ..core.enhanced_logger import get_enhanced_logger

router = APIRouter(prefix="/api/logs", tags=["logs"])

# Pydantic models for responses
class ErrorSummary(BaseModel):
    """Error summary response model."""
    total_errors: int
    error_counts: Dict[str, int]  # Fixed: was error_types
    error_details: Dict[str, List[Dict[str, Any]]]  # Fixed: was recent_errors and critical_errors

class PerformanceMetrics(BaseModel):
    """Performance metrics response model."""
    api_performance: Dict[str, Dict[str, Any]]  # Fixed: matches actual structure
    operation_performance: Dict[str, Dict[str, Any]]  # Fixed: matches actual structure

class UserActivity(BaseModel):
    """User activity response model."""
    total_requests: int
    unique_users: int
    requests_by_endpoint: Dict[str, int]
    requests_by_hour: Dict[str, int]

class SystemHealth(BaseModel):
    """System health response model."""
    status: str
    uptime: str
    error_rate: float
    average_response_time: float
    active_operations: int
    warnings: List[str]

def get_log_analyzer() -> LogAnalyzer:
    """Dependency to get log analyzer instance."""
    return LogAnalyzer()

@router.get("/errors", response_model=ErrorSummary)
async def get_error_summary(
    hours: int = Query(24, ge=1, le=168, description="Hours to analyze (1-168)"),
    analyzer: LogAnalyzer = Depends(get_log_analyzer)
):
    """Get error summary and analysis for the specified time period."""
    try:
        logger = get_enhanced_logger()
        
        with logger.correlation_context() as correlation_id:
            logger.log_operation_start("get_error_summary", correlation_id=correlation_id)            
            logger.info(f"Analyzing errors for the last {hours} hours")
            
            summary = analyzer.get_error_summary(hours_back=hours)
            
            logger.log_operation_end("get_error_summary", correlation_id=correlation_id)
            return ErrorSummary(**summary)
            
    except Exception as e:
        logger.error(f"Failed to get error summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to analyze errors")

@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(
    hours: int = Query(24, ge=1, le=168, description="Hours to analyze (1-168)"),
    analyzer: LogAnalyzer = Depends(get_log_analyzer)
):
    """Get performance metrics and timing analysis."""
    try:
        logger = get_enhanced_logger()
        
        with logger.correlation_context() as correlation_id:
            logger.log_operation_start("get_performance_metrics", correlation_id=correlation_id)
            logger.info(f"Analyzing performance metrics for the last {hours} hours")
            
            since = datetime.now() - timedelta(hours=hours)
            metrics = analyzer.get_performance_summary(hours_back=hours)
            
            logger.log_operation_end("get_performance_metrics", correlation_id=correlation_id)
            return PerformanceMetrics(**metrics)
            
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to analyze performance")

@router.get("/activity", response_model=UserActivity)
async def get_user_activity(
    hours: int = Query(24, ge=1, le=168, description="Hours to analyze (1-168)"),
    analyzer: LogAnalyzer = Depends(get_log_analyzer)
):
    """Get user activity and API usage statistics."""
    try:
        logger = get_enhanced_logger()
        
        with logger.correlation_context() as correlation_id:
            logger.log_operation_start("get_user_activity", correlation_id=correlation_id)
            logger.info(f"Analyzing user activity for the last {hours} hours")
            
            since = datetime.now() - timedelta(hours=hours)
            activity = analyzer.get_user_activity(hours_back=hours)
            
            logger.log_operation_end("get_user_activity", correlation_id=correlation_id)
            return UserActivity(**activity)
            
    except Exception as e:
        logger.error(f"Failed to get user activity: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to analyze user activity")

@router.get("/health", response_model=SystemHealth)
async def get_system_health(
    analyzer: LogAnalyzer = Depends(get_log_analyzer)
):
    """Get current system health status and warnings."""
    try:
        logger = get_enhanced_logger()
        
        with logger.correlation_context() as correlation_id:
            logger.log_operation_start("get_system_health", correlation_id=correlation_id)
            logger.info("Checking system health status")
            
            health = analyzer.get_system_health()
            
            logger.log_operation_end("get_system_health", correlation_id=correlation_id)
            return SystemHealth(**health)
            
    except Exception as e:
        logger.error(f"Failed to get system health: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to check system health")

@router.get("/search")
async def search_logs(
    query: str = Query(..., description="Search query for log content"),
    hours: int = Query(24, ge=1, le=168, description="Hours to search (1-168)"),
    level: Optional[str] = Query(None, description="Log level filter (debug, info, warning, error, critical)"),
    operation: Optional[str] = Query(None, description="Operation name filter"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    analyzer: LogAnalyzer = Depends(get_log_analyzer)
):
    """Search through log entries with various filters."""
    try:
        logger = get_enhanced_logger()
        
        with logger.correlation_context() as correlation_id:
            logger.log_operation_start("search_logs", correlation_id=correlation_id)
            logger.info(f"Searching logs: query='{query}', hours={hours}, level={level}")
            
            since = datetime.now() - timedelta(hours=hours)
            results = analyzer.search_logs(
                query=query,
                since=since,
                level=level,
                operation=operation,
                limit=limit
            )
            
            logger.log_operation_end("search_logs", correlation_id=correlation_id)
            return {
                "query": query,
                "total_results": len(results),
                "results": results
            }
            
    except Exception as e:
        logger.error(f"Failed to search logs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to search logs")

@router.get("/correlation/{correlation_id}")
async def get_correlation_trace(
    correlation_id: str,
    analyzer: LogAnalyzer = Depends(get_log_analyzer)
):
    """Get all log entries for a specific correlation ID to trace a request."""
    try:
        logger = get_enhanced_logger()
        
        with logger.correlation_context() as new_correlation_id:
            logger.log_operation_start("get_correlation_trace", correlation_id=new_correlation_id)
            logger.info(f"Tracing correlation ID: {correlation_id}")
            
            trace = analyzer.get_correlation_trace(correlation_id)
            
            logger.log_operation_end("get_correlation_trace", correlation_id=new_correlation_id)
            return {
                "correlation_id": correlation_id,
                "total_entries": len(trace),
                "trace": trace
            }
            
    except Exception as e:
        logger.error(f"Failed to get correlation trace: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to trace correlation")

@router.post("/cleanup")
async def cleanup_old_logs(
    days: int = Query(30, ge=7, le=365, description="Keep logs newer than this many days"),
    analyzer: LogAnalyzer = Depends(get_log_analyzer)
):
    """Clean up old log files to manage disk space."""
    try:
        logger = get_enhanced_logger()
        
        with logger.correlation_context() as correlation_id:
            logger.log_operation_start("cleanup_old_logs", correlation_id=correlation_id)
            logger.info(f"Cleaning up logs older than {days} days")
            
            cutoff_date = datetime.now() - timedelta(days=days)
            result = analyzer.cleanup_old_logs(cutoff_date)
            
            logger.log_operation_end("cleanup_old_logs", correlation_id=correlation_id)
            return {
                "cleaned_up": True,
                "cutoff_date": cutoff_date.isoformat(),
                "files_processed": result.get("files_processed", 0),
                "space_freed": result.get("space_freed", 0)
            }
            
    except Exception as e:
        logger.error(f"Failed to cleanup logs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to cleanup logs")

@router.get("/stats")
async def get_log_statistics(
    analyzer: LogAnalyzer = Depends(get_log_analyzer)
):
    """Get general statistics about the logging system."""
    try:
        logger = get_enhanced_logger()
        
        with logger.correlation_context() as correlation_id:
            logger.log_operation_start("get_log_statistics", correlation_id=correlation_id)
            logger.info("Getting logging system statistics")
            
            stats = analyzer.get_log_statistics()
            
            logger.log_operation_end("get_log_statistics", correlation_id=correlation_id)
            return stats
            
    except Exception as e:
        logger.error(f"Failed to get log statistics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get statistics")
