"""Main FastAPI application for SocioGraph.

This module initializes the FastAPI application and includes all routers.
"""

import sys
import time

# Check for help command early to avoid loading heavy dependencies
if "--help" in sys.argv or "-h" in sys.argv:
    import argparse
    
    parser = argparse.ArgumentParser(description="SocioGraph API Server")
    parser.add_argument(
        "--host", 
        default="127.0.0.1", 
        help="Host to bind the server to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind the server to (default: 8000)"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--workers", 
        type=int, 
        default=1, 
        help="Number of worker processes"
    )
    parser.add_argument(
        "--log-level", 
        default="info", 
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Log level (default: info)"
    )
    
    parser.print_help()
    sys.exit(0)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .core.logging_middleware import LoggingMiddleware


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Initialize enhanced logging early
    from .core.enhanced_logger import get_enhanced_logger
    logger = get_enhanced_logger()
    
    start_time = time.time()
    with logger.correlation_context() as correlation_id:
        logger.info(f"Initializing SocioRAG FastAPI application... [correlation_id: {correlation_id}]")
        logger.log_operation_start("app_initialization")
    
    from .api.ingest import router as ingest_router
    from .api.qa import router as qa_router
    from .api.history_new import router as history_router
    from .api.documents import router as documents_router
    from .api.search import router as search_router
    from .api.export import router as export_router
    from .api.admin import router as admin_router
    from .api.websocket_new import router as websocket_router
    from .api.logs import router as logs_router
    
    # Create FastAPI application
    app = FastAPI(
        title="SocioGraph API",
        description="SocioGraph: AI-powered document analysis and knowledge graph generation",
        version="0.2.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=[
            {
                "name": "ingest",
                "description": "Document ingestion endpoints for uploading and processing PDFs"
            },
            {
                "name": "qa",
                "description": "Question and Answer endpoints for interacting with the knowledge base"
            },
            {
                "name": "history",
                "description": "Query history and statistics endpoints"
            },
            {
                "name": "websocket",
                "description": "Real-time communication endpoints using WebSockets"
            },
            {
                "name": "documents",
                "description": "Document management endpoints"
            },
            {
                "name": "search",
                "description": "Search endpoints for finding content in the knowledge base"
            },
            {
                "name": "export",
                "description": "Export endpoints for retrieving data in various formats"
            },
            {
                "name": "admin",
                "description": "Administrative endpoints for system management"
            },
            {
                "name": "logs",
                "description": "Log analysis and monitoring endpoints"
            }
        ]
    )
    
    # Add logging middleware first
    app.add_middleware(LoggingMiddleware)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for development
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
        max_age=600,  # Cache preflight requests for 10 minutes
    )
    
    # Mount static files for serving saved PDFs
    import os
    from pathlib import Path
    
    saved_dir = Path("saved")
    if not saved_dir.exists():        # Try project root
        project_root = Path(__file__).parent.parent.parent
        saved_dir = project_root / "saved"
        if not saved_dir.exists():
            # Create it if it doesn't exist
            saved_dir.mkdir(parents=True, exist_ok=True)
    
    app.mount("/static/saved", StaticFiles(directory=str(saved_dir)), name="saved")

    # Include routers
    app.include_router(ingest_router)
    app.include_router(qa_router)
    app.include_router(history_router)
    app.include_router(documents_router)
    app.include_router(search_router)
    app.include_router(export_router)
    app.include_router(admin_router)
    app.include_router(websocket_router)
    app.include_router(logs_router)
    
    logger.info("All API routers registered successfully")

    @app.get("/")
    async def root():
        """Root endpoint for API health check."""
        return {"status": "ok", "message": "SocioGraph API is running"}
    
    duration = time.time() - start_time
    logger.log_operation_end("app_initialization", success=True, duration=duration)
    logger.info(f"SocioRAG FastAPI application initialization complete in {duration:.2f}s")
    return app


# Use lazy initialization to prevent double initialization during imports
# This is especially important when using uvicorn with --reload
def get_application():
    """Application factory function to create FastAPI app."""
    return create_app()

# Only initialize when actually needed (not during imports)
app = None

def _get_app():
    """Get the application instance, creating it if necessary."""
    global app
    if app is None:
        app = get_application()
    return app

# This allows uvicorn to import the app without immediate initialization
app = _get_app()


# CLI support for the application
def main():
    """Main CLI entry point for SocioGraph API server."""
    import argparse
    
    # Initialize enhanced logging early for startup messages
    from .core.enhanced_logger import get_enhanced_logger
    logger = get_enhanced_logger()
    
    parser = argparse.ArgumentParser(description="SocioGraph API Server")
    parser.add_argument(
        "--host", 
        default="127.0.0.1", 
        help="Host to bind the server to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind the server to (default: 8000)"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--workers", 
        type=int, 
        default=1, 
        help="Number of worker processes"
    )
    parser.add_argument(
        "--log-level", 
        default="info", 
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Log level (default: info)"
    )
    args = parser.parse_args()
    
    # Import uvicorn when starting the server
    import uvicorn
    
    logger.info("Starting SocioGraph API server...")
    logger.info(f"Server configuration: host={args.host}, port={args.port}, reload={args.reload}")
    logger.info(f"Log level: {args.log_level}")
    
    print(f"🚀 Starting SocioGraph API server...")
    print(f"📍 Server will be available at: http://{args.host}:{args.port}")
    print(f"📚 API documentation at: http://{args.host}:{args.port}/docs")
    print(f"🔧 Auto-reload: {'enabled' if args.reload else 'disabled'}")
    
    try:
        uvicorn.run(
            "backend.app.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers,
            log_level=args.log_level
        )
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Server startup failed: {str(e)}", exc_info=True)
        raise


# If this file is run directly, start the server
if __name__ == "__main__":
    main()