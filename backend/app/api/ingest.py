"""Ingest API router for SocioGraph.

This module provides API endpoints for:
1. Resetting the corpus (/reset)
2. Uploading PDF files (/upload)
"""

from fastapi import APIRouter, UploadFile, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
import json

from backend.app.core.config import get_config
from backend.app.ingest import reset_corpus
from backend.app.ingest.pipeline import process_all


router = APIRouter(
    prefix="",
    tags=["ingest"]
)


@router.post("/reset")
async def reset_endpoint():
    """Reset the corpus by clearing all data stores."""
    try:
        result = reset_corpus()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset corpus: {str(e)}")


@router.post("/upload")
async def upload(file: UploadFile, tasks: BackgroundTasks):
    """Upload a PDF file and process it.
    
    The file will be saved to the input directory and processed in the background.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:        # Get configuration
        cfg = get_config()
        
        # Ensure input directory exists
        cfg.INPUT_DIR.mkdir(exist_ok=True)
        
        # Save file
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
            
        dest = (cfg.INPUT_DIR / file.filename).with_suffix(".pdf")
        dest.write_bytes(await file.read())
        
        # Schedule processing
        tasks.add_task(process_all)
        
        return {
            "status": "uploaded",
            "file": dest.name,
            "message": "Processing started in the background"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/progress")
async def progress():
    """Stream progress updates from the ingestion pipeline."""
    
    async def progress_stream():
        """Generate progress updates as a stream."""
        for update in process_all():
            yield f"data: {json.dumps(update)}\n\n"
    
    return StreamingResponse(
        progress_stream(),
        media_type="text/event-stream"
    )