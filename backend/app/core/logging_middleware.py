"""FastAPI middleware for enhanced logging."""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .enhanced_logger import get_enhanced_logger, CorrelationContext


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation IDs and log API requests."""
    
    def __init__(self, app, skip_paths: list = None):
        super().__init__(app)
        self.skip_paths = skip_paths or ["/docs", "/redoc", "/openapi.json", "/favicon.ico"]
        self.logger = get_enhanced_logger()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for certain paths
        if any(request.url.path.startswith(path) for path in self.skip_paths):
            return await call_next(request)
        
        # Generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())[:8]
        
        # Set correlation context
        with self.logger.correlation_context(correlation_id):
            start_time = time.time()
            
            # Log request start
            self.logger.debug(
                f"Request started: {request.method} {request.url.path}",
                extra={
                    "http_method": request.method,
                    "endpoint": request.url.path,
                    "query_params": str(request.query_params),
                    "user_agent": request.headers.get("user-agent", "unknown"),
                    "client_ip": request.client.host if request.client else "unknown"
                }
            )
            
            try:
                response = await call_next(request)
                duration = time.time() - start_time
                
                # Log successful request
                self.logger.log_api_request(
                    method=request.method,
                    endpoint=request.url.path,
                    status_code=response.status_code,
                    duration=duration,
                    query_params=str(request.query_params) if request.query_params else None,
                    response_size=response.headers.get("content-length", "unknown")
                )
                
                # Add correlation ID to response headers
                response.headers["X-Correlation-ID"] = correlation_id
                
                return response
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Log failed request
                self.logger.error(
                    f"Request failed: {request.method} {request.url.path}",
                    extra={
                        "http_method": request.method,
                        "endpoint": request.url.path,
                        "duration_seconds": duration,
                        "error": str(e),
                        "error_type": type(e).__name__
                    },
                    exc_info=True
                )
                
                raise
