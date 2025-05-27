"""Ingest API router for SocioGraph.

This module provides API endpoints for:
1. Resetting the corpus (/reset)
2. Uploading PDF files (/upload)
3. Processing files in the input directory (/process)
4. Streaming progress updates (/progress)
"""

from fastapi import APIRouter, UploadFile, BackgroundTasks, HTTPException, status
from fastapi.responses import StreamingResponse
import json
import asyncio
import time
from typing import Dict, Any, List, AsyncGenerator
from concurrent.futures import ThreadPoolExecutor

from app.core.config import get_config
from app.ingest import reset_corpus
from app.ingest.pipeline import process_all
from app.core.singletons import LoggerSingleton

# Initialize logger
_logger = LoggerSingleton().get()

router = APIRouter(
    prefix="/api/ingest",
    tags=["ingest"],
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"}
    }
)


@router.post("/reset", 
            summary="Reset the corpus",
            description="Reset the corpus by clearing all data stores (vector store, database, etc).")
async def reset_endpoint():
    """Reset the corpus by clearing all data stores."""
    try:
        result = reset_corpus()
        return result
    except Exception as e:
        _logger.error(f"Failed to reset corpus: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reset corpus: {str(e)}")


@router.post("/upload",
            summary="Upload a PDF file",
            description="Upload a PDF file and process it in the background.")
async def upload(file: UploadFile, tasks: BackgroundTasks):
    """Upload a PDF file and process it.
    
    The file will be saved to the input directory and processed in the background.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Get configuration
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
        _logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/process",
            summary="Trigger document processing",
            description="Manually trigger processing of all files in the input directory.")
async def process_endpoint(tasks: BackgroundTasks):
    """Manually trigger processing of all files in the input directory.
    
    This endpoint will start background processing of all PDF files
    found in the configured input directory.
    """
    try:
        # Schedule processing
        tasks.add_task(process_all)
        
        return {
            "status": "started",
            "message": "Processing started in the background"
        }
    except Exception as e:
        _logger.error(f"Failed to start processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")


async def sync_to_async_generator(sync_generator):
    """Convert a synchronous generator to an async generator."""
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        # Create a list of all items in the generator - this executes the generator
        items = await loop.run_in_executor(pool, lambda: list(sync_generator))
        for item in items:
            yield item


@router.get("/progress",
           summary="Stream processing progress",
           description="Stream progress updates from the ingestion pipeline as Server-Sent Events (SSE).")
async def progress():
    """Stream progress updates from the ingestion pipeline.
    
    Returns Server-Sent Events (SSE) with progress information.
    """
    
    async def progress_stream():
        """Generate progress updates as a stream with heartbeats."""
        heartbeat_interval = 5  # seconds
        last_heartbeat = time.time()
        
        try:
            # Stream updates with heartbeats
            async for update in sync_to_async_generator(process_all()):
                # Send the actual update
                yield f"data: {json.dumps(update)}\n\n"
                
                # Add heartbeat if needed
                current_time = time.time()
                if current_time - last_heartbeat > heartbeat_interval:
                    last_heartbeat = current_time
                    yield f"event: heartbeat\ndata: {current_time}\n\n"
                    
            # Final heartbeat when done
            yield f"event: heartbeat\ndata: {time.time()}\n\n"
            
        except Exception as e:
            _logger.error(f"Error in progress stream: {str(e)}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        progress_stream(),
        media_type="text/event-stream"
    )
