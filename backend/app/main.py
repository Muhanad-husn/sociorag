"""Main FastAPI application for SocioGraph.

This module initializes the FastAPI application and includes all routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.ingest import router as ingest_router


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

# Include routers
app.include_router(ingest_router)


@app.get("/")
async def root():
    """Root endpoint for API health check."""
    return {"status": "ok", "message": "SocioGraph API is running"}


# If this file is run directly, start the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)