"""Saved Files API endpoints for SocioGraph.

This module provides API endpoints for:
- Listing saved PDF files and documents
- Getting file metadata
- Managing saved files
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.core.config import get_config
from backend.app.core.singletons import LoggerSingleton

_logger = LoggerSingleton().get()

router = APIRouter(prefix="/api/saved", tags=["saved"])


class SavedFileInfo(BaseModel):
    """Information about a saved file."""
    filename: str
    size: int
    created_at: datetime
    modified_at: datetime
    file_type: str
    download_url: str


class SavedFilesResponse(BaseModel):
    """Response model for saved files list."""
    files: List[SavedFileInfo]
    total_count: int
    total_size: int


@router.get("/files", response_model=SavedFilesResponse)
async def list_saved_files(
    sort_by: str = "modified_at",
    sort_order: str = "desc"
) -> SavedFilesResponse:
    """List saved PDF files in the saved directory with sorting options."""
    try:
        cfg = get_config()
        
        # Use the saved directory from config
        saved_dir = cfg.SAVED_DIR
        
        if not saved_dir.exists():
            _logger.warning(f"Saved directory does not exist: {saved_dir}")
            return SavedFilesResponse(files=[], total_count=0, total_size=0)
        
        files = []
        total_size = 0
        
        # Iterate through PDF files only in the saved directory
        for file_path in saved_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() == '.pdf':
                try:
                    # Get file stats
                    stat = file_path.stat()
                    
                    # Create file info
                    file_info = SavedFileInfo(
                        filename=file_path.name,
                        size=stat.st_size,
                        created_at=datetime.fromtimestamp(stat.st_ctime),
                        modified_at=datetime.fromtimestamp(stat.st_mtime),
                        file_type=".pdf",
                        download_url=f"/static/saved/{file_path.name}"
                    )
                    
                    files.append(file_info)
                    total_size += stat.st_size
                    
                except (OSError, PermissionError) as e:
                    _logger.warning(f"Could not access file {file_path}: {e}")
                    continue
        
        # Sort files based on parameters
        reverse = sort_order.lower() == "desc"
        if sort_by == "filename":
            files.sort(key=lambda x: x.filename.lower(), reverse=reverse)
        elif sort_by == "size":
            files.sort(key=lambda x: x.size, reverse=reverse)
        elif sort_by == "created_at":
            files.sort(key=lambda x: x.created_at, reverse=reverse)
        elif sort_by == "modified_at":
            files.sort(key=lambda x: x.modified_at, reverse=reverse)
        else:
            # Default to modified_at descending
            files.sort(key=lambda x: x.modified_at, reverse=True)
        
        _logger.info(f"Listed {len(files)} saved PDF files (total size: {total_size} bytes)")
        
        return SavedFilesResponse(
            files=files,
            total_count=len(files),
            total_size=total_size
        )
        
    except Exception as e:
        _logger.error(f"Failed to list saved files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list saved files: {str(e)}")


@router.get("/files/{filename}")
async def get_saved_file_info(filename: str) -> SavedFileInfo:
    """Get information about a specific saved file."""
    try:
        cfg = get_config()
        saved_dir = cfg.SAVED_DIR
        file_path = saved_dir / filename
        
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")
        
        stat = file_path.stat()
        file_type = file_path.suffix.lower() or "unknown"
        
        file_info = SavedFileInfo(
            filename=file_path.name,
            size=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            file_type=file_type,
            download_url=f"/static/saved/{file_path.name}"
        )
        
        _logger.info(f"Retrieved info for saved file: {filename}")
        return file_info
        
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Failed to get file info for {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get file info: {str(e)}")


@router.get("/view/{filename}")
async def view_saved_file(filename: str):
    """Serve a saved PDF file with headers optimized for viewing in browser."""
    try:
        cfg = get_config()
        saved_dir = cfg.SAVED_DIR
        file_path = saved_dir / filename
        
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")
        
        # Only serve PDF files through this endpoint
        if not filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files can be viewed")
        
        # Read the file content
        file_content = file_path.read_bytes()
        
        # Return with headers that encourage viewing instead of downloading
        from fastapi.responses import Response
        return Response(
            content=file_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename={filename}",
                "Content-Type": "application/pdf",
                "Cache-Control": "public, max-age=3600"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Failed to serve file {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to serve file: {str(e)}")
