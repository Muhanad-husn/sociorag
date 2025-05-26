"""Main FastAPI application for SocioGraph.

This module initializes the FastAPI application and includes all routers.
"""

import sys

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


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    from backend.app.api.ingest import router as ingest_router
    from backend.app.api.qa import router as qa_router
    
    # Create FastAPI application
    app = FastAPI(
        title="SocioGraph API",
        description="SocioGraph: AI-powered document analysis and knowledge graph",
        version="0.1.0"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for development
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files for serving saved PDFs
    app.mount("/static/saved", StaticFiles(directory="saved"), name="saved")

    # Include routers
    app.include_router(ingest_router)
    app.include_router(qa_router)

    @app.get("/")
    async def root():
        """Root endpoint for API health check."""
        return {"status": "ok", "message": "SocioGraph API is running"}
    
    return app


# Create the app instance (will be imported by uvicorn)
app = create_app()


# CLI support for the application
def main():
    """Main CLI entry point for SocioGraph API server."""
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
    
    args = parser.parse_args()
    
    # Import uvicorn when starting the server
    import uvicorn
    
    print(f"🚀 Starting SocioGraph API server...")
    print(f"📍 Server will be available at: http://{args.host}:{args.port}")
    print(f"📚 API documentation at: http://{args.host}:{args.port}/docs")
    print(f"🔧 Auto-reload: {'enabled' if args.reload else 'disabled'}")
    
    uvicorn.run(
        "backend.app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level=args.log_level
    )


# If this file is run directly, start the server
if __name__ == "__main__":
    main()