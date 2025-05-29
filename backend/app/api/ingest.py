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

from backend.app.core.config import get_config
from backend.app.ingest import reset_corpus
from backend.app.ingest.pipeline import process_all
from backend.app.core.singletons import LoggerSingleton
from backend.app.core.process_state import get_process_manager, ProcessStatus

# Initialize logger and process manager
_logger = LoggerSingleton().get()
_process_manager = get_process_manager()


def run_processing_with_state_management():
    """Run the processing pipeline with proper state management."""
    process_id = "ingest_pipeline"
    
    # Check if already running
    if _process_manager.is_running(process_id):
        _logger.warning("Ingestion process is already running")
        return
    
    # Start the process
    if not _process_manager.start_process(process_id):
        _logger.error("Failed to start ingestion process")
        return
    
    try:
        # Create and store the generator
        generator = process_all()
        _process_manager.set_active_generator(process_id, generator)
        
        # Consume the generator to actually run the process
        for update in generator:
            # Update state based on the progress update
            if "percent" in update:
                _process_manager.update_state(
                    process_id,
                    progress=update["percent"],
                    phase=update.get("phase", ""),
                    message=update.get("message", ""),
                    current_file=update.get("file", "")
                )
        
        # Mark as completed
        _process_manager.complete_process(process_id, success=True)
        
    except Exception as e:
        _logger.error(f"Error in processing pipeline: {str(e)}")
        _process_manager.complete_process(process_id, success=False, error_message=str(e))


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
        # Reset the process state first
        _process_manager.reset_process("ingest_pipeline")
        
        # Then reset the corpus
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
        tasks.add_task(run_processing_with_state_management)
        
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
        tasks.add_task(run_processing_with_state_management)
        
        return {
            "status": "started",
            "message": "Processing started in the background"
        }
    except Exception as e:
        _logger.error(f"Failed to start processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")


@router.get("/progress",
           summary="Stream processing progress",
           description="Stream progress updates from the ingestion pipeline as Server-Sent Events (SSE).")
async def progress():
    """Stream progress updates from the ingestion pipeline.
    
    Returns Server-Sent Events (SSE) with progress information.
    This endpoint does NOT start processing - it only streams the status of existing processes.
    """
    
    async def progress_stream():
        """Generate progress updates as a stream with heartbeats."""
        process_id = "ingest_pipeline"
        heartbeat_interval = 5  # seconds
        last_heartbeat = time.time()
        
        try:
            # Check if there's an active process
            while True:
                current_time = time.time()
                
                # Get current state
                state = _process_manager.get_state(process_id)
                
                # Send state update
                yield f"data: {json.dumps(state.to_dict())}\n\n"
                
                # If process is completed or error, send final update and exit
                if state.status in [ProcessStatus.COMPLETED, ProcessStatus.ERROR]:
                    yield f"event: complete\ndata: {json.dumps(state.to_dict())}\n\n"
                    break
                
                # Add heartbeat if needed
                if current_time - last_heartbeat > heartbeat_interval:
                    last_heartbeat = current_time
                    yield f"event: heartbeat\ndata: {current_time}\n\n"
                
                # Wait a bit before next update
                await asyncio.sleep(1)
                    
        except Exception as e:
            _logger.error(f"Error in progress stream: {str(e)}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        progress_stream(),
        media_type="text/event-stream"
    )
