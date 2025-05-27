"""Document Management API endpoints for SocioGraph.

This module provides comprehensive document management functionality including:
- Document upload and processing
- Document metadata and status tracking
- Document analytics and entity extraction
- Document deletion and management
"""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, Form, Query, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

from backend.app.core.config import get_config
from backend.app.core.singletons import LoggerSingleton, SQLiteSingleton
from backend.app.ingest.pipeline import process_all
from backend.app.ingest import reset_corpus

_logger = LoggerSingleton().get()

router = APIRouter(prefix="/api/documents", tags=["documents"])


# Response Models
class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    document_id: str
    filename: str
    status: str
    message: str
    processing_started: bool


class DocumentInfo(BaseModel):
    """Document information model."""
    document_id: str
    filename: str
    upload_time: datetime
    file_size: int
    status: str
    metadata: Optional[Dict[str, Any]] = None
    processing_stats: Optional[Dict[str, Any]] = None


class DocumentList(BaseModel):
    """List of documents with pagination."""
    documents: List[DocumentInfo]
    total: int
    limit: int
    offset: int


class ProcessingStatus(BaseModel):
    """Document processing status."""
    document_id: str
    status: str
    progress: float
    message: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class DocumentAnalytics(BaseModel):
    """Document analytics model."""
    document_id: str
    total_chunks: int
    total_entities: int
    total_relationships: int
    entity_types: Dict[str, int]
    processing_time: Optional[float] = None


class EntityList(BaseModel):
    """List of entities from a document."""
    entities: List[Dict[str, Any]]
    total: int
    document_id: str


class StatusResponse(BaseModel):
    """Generic status response."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


# Global processing status tracking
_processing_status: Dict[str, ProcessingStatus] = {}


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    process_immediately: bool = Form(True)
) -> DocumentUploadResponse:
    """Upload and optionally process a document.
    
    Args:
        file: The PDF file to upload
        metadata: Optional JSON metadata for the document
        process_immediately: Whether to start processing immediately
    
    Returns:
        DocumentUploadResponse with upload status and document ID
    """
    # Validate file
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        cfg = get_config()
        
        # Generate document ID
        document_id = str(uuid4())
        
        # Ensure input directory exists
        cfg.INPUT_DIR.mkdir(exist_ok=True)
        
        # Save file with document ID prefix
        safe_filename = f"{document_id}_{file.filename}"
        file_path = cfg.INPUT_DIR / safe_filename
        
        # Save uploaded file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Parse metadata if provided
        parsed_metadata = None
        if metadata:
            try:
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                _logger.warning(f"Invalid metadata JSON for document {document_id}")
          # Store document info in database
        db_conn = SQLiteSingleton().get()
        upload_time = datetime.now()
        
        # Create documents table if it doesn't exist
        cursor = db_conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                upload_time TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                status TEXT DEFAULT 'uploaded',
                metadata TEXT,
                processing_stats TEXT
            )
        """)
        
        # Insert document record
        cursor.execute("""
            INSERT INTO documents 
            (document_id, filename, original_filename, upload_time, file_size, status, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (document_id, safe_filename, file.filename, upload_time.isoformat(), 
              len(content), 'uploaded', json.dumps(parsed_metadata) if parsed_metadata else None))
        db_conn.commit()
        cursor.close()
        
        _logger.info(f"Document uploaded: {document_id} ({file.filename})")
        
        # Start processing if requested
        processing_started = False
        if process_immediately:
            # Initialize processing status
            _processing_status[document_id] = ProcessingStatus(
                document_id=document_id,
                status="queued",
                progress=0.0,
                message="Processing queued",
                started_at=datetime.now()
            )
            
            # Start background processing
            background_tasks.add_task(_process_document, document_id, file_path)
            processing_started = True
            _logger.info(f"Started background processing for document {document_id}")
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            status="uploaded",
            message="Document uploaded successfully",
            processing_started=processing_started
        )
        
    except Exception as e:
        _logger.error(f"Failed to upload document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/{document_id}", response_model=DocumentInfo)
async def get_document(document_id: str) -> DocumentInfo:
    """Get document information and metadata."""
    try:
        db_conn = SQLiteSingleton().get()
        
        # Query document info
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT document_id, filename, original_filename, upload_time, 
                   file_size, status, metadata, processing_stats
            FROM documents WHERE document_id = ?
        """, (document_id,))
        
        result = cursor.fetchall()
        cursor.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc = result[0]
        
        # Parse metadata and stats
        metadata = json.loads(doc[6]) if doc[6] else None
        processing_stats = json.loads(doc[7]) if doc[7] else None
        
        return DocumentInfo(
            document_id=doc[0],
            filename=doc[2],  # original filename
            upload_time=datetime.fromisoformat(doc[3]),
            file_size=doc[4],
            status=doc[5],
            metadata=metadata,
            processing_stats=processing_stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Failed to get document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document: {str(e)}")


@router.get("/", response_model=DocumentList)
async def list_documents(
    status: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0)
) -> DocumentList:
    """List documents with filtering and pagination."""
    try:
        db_conn = SQLiteSingleton().get()
        
        # Build query with optional status filter
        where_clause = "WHERE status = ?" if status else ""
        params = [status] if status else []
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM documents {where_clause}"
        cursor = db_conn.cursor()
        cursor.execute(count_query, params)
        count_result = cursor.fetchone()
        total = count_result[0] if count_result else 0
        
        # Get documents with pagination
        query = f"""
            SELECT document_id, filename, original_filename, upload_time, 
                   file_size, status, metadata, processing_stats
            FROM documents {where_clause}
            ORDER BY upload_time DESC
            LIMIT ? OFFSET ?
        """
        # Convert integers to strings to satisfy the type system
        cursor.execute(query, params + [str(limit), str(offset)])
        results = cursor.fetchall()
        cursor.close()
        
        documents = []
        for doc in results:
            metadata = json.loads(doc[6]) if doc[6] else None
            processing_stats = json.loads(doc[7]) if doc[7] else None
            
            documents.append(DocumentInfo(
                document_id=doc[0],
                filename=doc[2],  # original filename
                upload_time=datetime.fromisoformat(doc[3]),
                file_size=doc[4],
                status=doc[5],
                metadata=metadata,
                processing_stats=processing_stats
            ))
        
        return DocumentList(
            documents=documents,
            total=total,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        _logger.error(f"Failed to list documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.get("/{document_id}/status", response_model=ProcessingStatus)
async def get_processing_status(document_id: str) -> ProcessingStatus:
    """Get document processing status."""
    # Check if processing is in progress
    if document_id in _processing_status:
        return _processing_status[document_id]
      # Check database status
    try:
        db_conn = SQLiteSingleton().get()
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT status, processing_stats FROM documents WHERE document_id = ?
        """, (document_id,))
        result = cursor.fetchall()
        cursor.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="Document not found")
        
        status, stats_json = result[0]
        stats = json.loads(stats_json) if stats_json else {}
        
        # Safely handle the completed_at value, ensuring it's a string before passing to fromisoformat
        completed_at = None
        if stats.get('completed_at'):
            completed_at_str = str(stats.get('completed_at'))
            completed_at = datetime.fromisoformat(completed_at_str)        
        return ProcessingStatus(
            document_id=document_id,
            status=status,
            progress=100.0 if status == "processed" else 0.0,
            message=f"Document status: {status}",
            completed_at=completed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Failed to get processing status for {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.delete("/{document_id}")
async def delete_document(document_id: str) -> StatusResponse:
    """Delete a document and associated data."""
    try:
        cfg = get_config()
        db_conn = SQLiteSingleton().get()
        
        # Get document info
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT filename FROM documents WHERE document_id = ?
        """, (document_id,))
        result = cursor.fetchall()
        
        if not result:
            raise HTTPException(status_code=404, detail="Document not found")
        
        filename = result[0][0]
        
        # Delete file if it exists
        file_path = cfg.INPUT_DIR / filename
        if file_path.exists():
            file_path.unlink()
            _logger.info(f"Deleted file: {file_path}")
        
        # Delete from database
        cursor.execute("DELETE FROM documents WHERE document_id = ?", (document_id,))
        db_conn.commit()
        cursor.close()
        
        # Remove from processing status if present
        if document_id in _processing_status:
            del _processing_status[document_id]
        
        _logger.info(f"Deleted document: {document_id}")
        
        return StatusResponse(
            success=True,
            message="Document deleted successfully",
            data={"document_id": document_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Failed to delete document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@router.get("/{document_id}/analytics", response_model=DocumentAnalytics)
async def get_document_analytics(document_id: str) -> DocumentAnalytics:
    """Get analytics for a specific document."""
    try:
        db_conn = SQLiteSingleton().get()
        cursor = db_conn.cursor()
        
        # Verify document exists
        cursor.execute("""
            SELECT processing_stats FROM documents WHERE document_id = ?
        """, (document_id,))
        doc_result = cursor.fetchone()
        
        if not doc_result:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get processing stats
        stats_json = doc_result[0]
        processing_stats = json.loads(stats_json) if stats_json else {}
        
        # Get entity counts by type
        cursor.execute("""
            SELECT entity_type, COUNT(*) 
            FROM entity 
            WHERE source_document = ?
            GROUP BY entity_type
        """, (document_id,))
        entity_counts = cursor.fetchall() or []
        
        entity_types = {row[0]: row[1] for row in entity_counts}
        total_entities = sum(entity_types.values())
        
        # Get relationship count
        cursor.execute("""
            SELECT COUNT(*) FROM relation 
            WHERE source_document = ?
        """, (document_id,))
        rel_result = cursor.fetchone()
        total_relationships = rel_result[0] if rel_result else 0
        cursor.close()
        
        return DocumentAnalytics(
            document_id=document_id,
            total_chunks=processing_stats.get('total_chunks', 0),
            total_entities=total_entities,
            total_relationships=total_relationships,
            entity_types=entity_types,
            processing_time=processing_stats.get('processing_time')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Failed to get analytics for document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


async def _process_document(document_id: str, file_path: Path):
    """Background task to process a document."""
    try:
        # Update status to processing
        _processing_status[document_id].status = "processing"
        _processing_status[document_id].message = "Processing document..."
        _processing_status[document_id].progress = 10.0
        
        # Update database status
        db_conn = SQLiteSingleton().get()
        cursor = db_conn.cursor()
        cursor.execute("""
            UPDATE documents SET status = 'processing' WHERE document_id = ?
        """, (document_id,))
        db_conn.commit()
        
        start_time = time.time()
        
        # Process the document using the existing pipeline
        # Note: This assumes the process_all function can handle a single file
        _processing_status[document_id].progress = 50.0
        _processing_status[document_id].message = "Extracting entities and relationships..."
        
        # Run the processing pipeline
        result_obj = await asyncio.to_thread(process_all)
        
        # Extract data from the result (assuming it's a dictionary)
        if isinstance(result_obj, dict):
            result = result_obj
        else:
            # If it's a Generator or another type, try to convert to dict
            result = {"chunks_created": 0, "entities_created": 0}
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Update final status
        _processing_status[document_id].status = "completed"
        _processing_status[document_id].progress = 100.0
        _processing_status[document_id].message = "Processing completed successfully"
        _processing_status[document_id].completed_at = datetime.now()
        
        # Update database with completion
        processing_stats = {
            "processing_time": processing_time,
            "completed_at": datetime.now().isoformat(),
            "total_chunks": result.get("chunks_created", 0) if isinstance(result, dict) else 0,
            "total_entities": result.get("entities_created", 0) if isinstance(result, dict) else 0
        }
        
        cursor.execute("""
            UPDATE documents 
            SET status = 'processed', processing_stats = ?
            WHERE document_id = ?
        """, (json.dumps(processing_stats), document_id))
        db_conn.commit()
        cursor.close()
        
        _logger.info(f"Document processing completed for {document_id} in {processing_time:.2f}s")
        
    except Exception as e:
        # Update error status
        _processing_status[document_id].status = "error"
        _processing_status[document_id].message = f"Processing failed: {str(e)}"
        _processing_status[document_id].error = str(e)
        
        # Update database with error
        db_conn = SQLiteSingleton().get()
        cursor = db_conn.cursor()
        cursor.execute("""
            UPDATE documents SET status = 'error' WHERE document_id = ?
        """, (document_id,))
        db_conn.commit()
        cursor.close()
        
        _logger.error(f"Document processing failed for {document_id}: {str(e)}")
