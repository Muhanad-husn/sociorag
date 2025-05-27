"""History API router for SocioGraph.

This module provides API endpoints for:
1. Retrieving query history (/history)
2. Getting specific history records
3. Filtering and pagination support
"""

from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, Path
from pydantic import BaseModel
from datetime import datetime

from app.answer.history import get_recent_history, get_history_stats, cleanup_old_history
from app.core.singletons import LoggerSingleton

_logger = LoggerSingleton().get()

router = APIRouter(
    prefix="/api/history",
    tags=["history"]
)


class HistoryRecord(BaseModel):
    """History record response model."""
    id: int
    query: str
    timestamp: datetime
    token_count: int
    context_count: int
    metadata: dict


class HistoryResponse(BaseModel):
    """History response with pagination."""
    records: List[HistoryRecord]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


# NOTE: Order matters in FastAPI - more specific routes should come first
@router.get("/stats", description="Get statistics about query history")
async def get_history_stats_endpoint():
    """Get history statistics."""
    try:
        stats = get_history_stats()
        return stats
        
    except Exception as e:
        _logger.error(f"Failed to get history stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get history stats: {str(e)}")


@router.delete("/clear", description="Clear all history records")
async def clear_history_endpoint():
    """Clear all history records."""
    try:
        # Use the existing cleanup function with limit 0 to remove all records
        removed_count = cleanup_old_history(max_records=0)
        
        return {
            "status": "success",
            "message": f"All history records cleared ({removed_count} records removed)"
        }
        
    except Exception as e:
        _logger.error(f"Failed to clear history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear history: {str(e)}")


@router.get("/", response_model=HistoryResponse)
async def get_history_endpoint(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Records per page"),
    search: Optional[str] = Query(None, description="Search in queries")
):
    """Retrieve paginated query history.
    
    Returns a paginated list of query history records with optional search filtering.
    """
    try:
        # Get all history records
        all_records = get_recent_history()
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            all_records = [
                r for r in all_records 
                if search_lower in r.get('query', '').lower()
            ]
        
        # Calculate pagination
        total = len(all_records)
        offset = (page - 1) * per_page
        records = all_records[offset:offset + per_page]
        
        # Convert to response models
        history_records = []
        for i, record in enumerate(records):
            # Create a unique ID based on position (since JSONL doesn't have built-in IDs)
            record_id = offset + i + 1
            
            # Parse timestamp
            timestamp = record.get('datetime')
            if timestamp:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                timestamp = datetime.now()
            
            history_records.append(HistoryRecord(
                id=record_id,
                query=record.get('query', ''),
                timestamp=timestamp,
                token_count=record.get('token_count', 0),
                context_count=record.get('context_count', 0),
                metadata=record.get('metadata', {})
            ))
        
        return HistoryResponse(
            records=history_records,
            total=total,
            page=page,
            per_page=per_page,
            has_next=(offset + per_page) < total,
            has_prev=page > 1
        )
        
    except Exception as e:
        _logger.error(f"Failed to retrieve history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")


@router.get("/record/{record_id}", response_model=HistoryRecord)
async def get_history_record_endpoint(record_id: int = Path(..., description="The ID of the history record to retrieve")):
    """Retrieve a specific history record by ID."""
    try:
        # Get all history records
        all_records = get_recent_history()
        
        # Check if record_id is valid (1-based indexing)
        if record_id < 1 or record_id > len(all_records):
            raise HTTPException(status_code=404, detail="History record not found")
        
        # Get the specific record (convert to 0-based index)
        record = all_records[record_id - 1]
        
        # Parse timestamp
        timestamp = record.get('datetime')
        if timestamp:
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            timestamp = datetime.now()
        
        return HistoryRecord(
            id=record_id,
            query=record.get('query', ''),
            timestamp=timestamp,
            token_count=record.get('token_count', 0),
            context_count=record.get('context_count', 0),
            metadata=record.get('metadata', {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Failed to retrieve history record {record_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history record: {str(e)}")


@router.delete("/record/{record_id}")
async def delete_history_record_endpoint(record_id: int = Path(..., description="The ID of the history record to delete")):
    """Delete a specific history record by ID."""
    try:
        # Get all history records
        all_records = get_recent_history()
        
        # Check if record_id is valid (1-based indexing)
        if record_id < 1 or record_id > len(all_records):
            raise HTTPException(status_code=404, detail="History record not found")
        
        # Note: JSONL format doesn't support individual record deletion easily
        # This would require rewriting the entire file
        # For now, return a message indicating this limitation
        return {
            "status": "not_implemented",
            "message": f"Individual record deletion not implemented for JSONL format. Use clear all history instead.",
            "record_id": record_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Failed to delete history record {record_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete history record: {str(e)}")