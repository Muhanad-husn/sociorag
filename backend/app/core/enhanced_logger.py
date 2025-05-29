"""Enhanced logging system for SocioRAG.

This module provides structured logging, correlation IDs, and performance monitoring
capabilities to improve observability and debugging.
"""

import json
import logging
import logging.handlers
import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Optional, Union
from functools import wraps
import threading
from pathlib import Path

from .config import get_config
from .singletons import LoggerSingleton


class CorrelationFilter(logging.Filter):
    """Add correlation ID to log records."""
    
    def filter(self, record):
        correlation_id = getattr(CorrelationContext, 'correlation_id', None)
        record.correlation_id = correlation_id or 'none'
        return True


class PerformanceFilter(logging.Filter):
    """Add performance metrics to log records."""
    
    def filter(self, record):
        # Add memory usage if available
        try:
            import psutil
            process = psutil.Process()
            record.memory_mb = round(process.memory_info().rss / 1024 / 1024, 1)
        except (ImportError, Exception):
            record.memory_mb = 0
        return True


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        log_entry = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'correlation_id': getattr(record, 'correlation_id', 'none'),
            'memory_mb': getattr(record, 'memory_mb', 0)
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage',
                          'correlation_id', 'memory_mb']:
                log_entry[key] = value
                
        return json.dumps(log_entry, default=str, ensure_ascii=False)


class CorrelationContext:
    """Thread-local storage for correlation IDs."""
    _local = threading.local()
    
    @classmethod
    @property
    def correlation_id(cls) -> Optional[str]:
        return getattr(cls._local, 'correlation_id', None)
    
    @classmethod
    def set_correlation_id(cls, correlation_id: str):
        cls._local.correlation_id = correlation_id
    
    @classmethod
    def clear_correlation_id(cls):
        if hasattr(cls._local, 'correlation_id'):
            delattr(cls._local, 'correlation_id')


class EnhancedLogger:
    """Enhanced logger with structured logging and correlation support."""
    
    def __init__(self):
        self._base_logger = LoggerSingleton().get()
        self._setup_enhanced_logging()
    
    def _setup_enhanced_logging(self):
        """Setup enhanced logging features."""
        config = get_config()
        
        if not config.ENHANCED_LOGGING_ENABLED:
            return
        
        logs_dir = config.BASE_DIR / "logs"
        logs_dir.mkdir(exist_ok=True)
          # Add structured logging handler for JSON logs with UTF-8 encoding
        if config.LOG_STRUCTURED_FORMAT:
            json_handler = logging.handlers.RotatingFileHandler(
                logs_dir / "sociorag_structured.log",
                maxBytes=config.LOG_MAX_FILE_SIZE_MB * 1024 * 1024,
                backupCount=config.LOG_ROTATION_BACKUP_COUNT,
                encoding='utf-8'
            )
            json_handler.setLevel(logging.DEBUG)
            json_handler.setFormatter(StructuredFormatter())
            
            if config.LOG_CORRELATION_ENABLED:
                json_handler.addFilter(CorrelationFilter())
            
            if config.LOG_PERFORMANCE_TRACKING:
                json_handler.addFilter(PerformanceFilter())
            
            # Only add if not already present
            if not any(isinstance(h, logging.handlers.RotatingFileHandler) 
                      and 'structured' in str(h.baseFilename) 
                      for h in self._base_logger.handlers):
                self._base_logger.addHandler(json_handler)
    
    @contextmanager
    def correlation_context(self, correlation_id: Optional[str] = None):
        """Context manager for correlation ID."""
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())[:8]
        
        CorrelationContext.set_correlation_id(correlation_id)
        try:
            yield correlation_id
        finally:
            CorrelationContext.clear_correlation_id()
    
    def log_operation_start(self, operation: str, **kwargs):
        """Log the start of an operation."""
        self._base_logger.info(
            f"Starting operation: {operation}",
            extra={
                'operation': operation,
                'operation_phase': 'start',
                **kwargs
            }
        )
    
    def log_operation_end(self, operation: str, **kwargs):
        """Log the end of an operation."""
        success = kwargs.get('success', True)
        duration = kwargs.get('duration')
        
        level = logging.INFO if success else logging.ERROR
        duration_text = f" ({duration:.2f}s)" if duration is not None else ""
        
        self._base_logger.log(
            level,
            f"Operation {'completed' if success else 'failed'}: {operation}{duration_text}",
            extra={
                'operation': operation,
                'operation_phase': 'end',
                **kwargs
            }
        )
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = '', **kwargs):
        """Log a performance metric."""
        self._base_logger.info(
            f"Performance metric: {metric_name} = {value}{unit}",
            extra={
                'metric_name': metric_name,
                'metric_value': value,
                'metric_unit': unit,
                'metric_type': 'performance',
                **kwargs
            }
        )
    
    def log_user_action(self, action: str, user_id: Optional[str] = None, **kwargs):
        """Log a user action."""
        self._base_logger.info(
            f"User action: {action}",
            extra={
                'action': action,
                'user_id': user_id or 'anonymous',
                'action_type': 'user',
                **kwargs
            }
        )
    
    def log_config_change(self, setting: str, old_value: Any, new_value: Any, user_id: Optional[str] = None):
        """Log a configuration change."""
        self._base_logger.info(
            f"Configuration changed: {setting}",
            extra={
                'setting': setting,
                'old_value': str(old_value),
                'new_value': str(new_value),
                'user_id': user_id or 'system',
                'change_type': 'configuration'
            }
        )
    
    def log_api_request(self, method: str, endpoint: str, status_code: int, 
                       duration: float, user_id: Optional[str] = None, **kwargs):
        """Log an API request."""
        level = logging.INFO if 200 <= status_code < 400 else logging.WARNING
        self._base_logger.log(
            level,
            f"API {method} {endpoint} -> {status_code} ({duration:.3f}s)",
            extra={
                'http_method': method,
                'endpoint': endpoint,
                'status_code': status_code,
                'duration_seconds': duration,
                'user_id': user_id or 'anonymous',
                'request_type': 'api',
                **kwargs
            }
        )
    
    # Delegate standard logging methods
    def debug(self, msg, *args, **kwargs):
        return self._base_logger.debug(msg, *args, **kwargs)
    
    def info(self, msg, *args, **kwargs):
        return self._base_logger.info(msg, *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        return self._base_logger.warning(msg, *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        return self._base_logger.error(msg, *args, **kwargs)
    
    def critical(self, msg, *args, **kwargs):
        return self._base_logger.critical(msg, *args, **kwargs)


def timed_operation(operation_name: Optional[str] = None):
    """Decorator to automatically log operation timing."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            logger = get_enhanced_logger()
            
            start_time = time.time()
            logger.log_operation_start(name)
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.log_operation_end(name, success=True, duration=duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.log_operation_end(name, success=False, duration=duration, error=str(e))
                raise
        
        return wrapper
    return decorator


# Singleton instance
_enhanced_logger: Optional[EnhancedLogger] = None


def get_enhanced_logger() -> EnhancedLogger:
    """Get the enhanced logger singleton."""
    global _enhanced_logger
    if _enhanced_logger is None:
        _enhanced_logger = EnhancedLogger()
    return _enhanced_logger


def get_logger():
    """Backward compatibility - returns the enhanced logger."""
    return get_enhanced_logger()


def log_operation_time(operation_name: Optional[str] = None):
    """Alias for timed_operation decorator for backward compatibility."""
    return timed_operation(operation_name)
