"""Export API endpoints for SocioGraph.

This module provides data export functionality including:
- PDF report generation
- History export in various formats
- Entity and relationship data export
- Analytics and summary reports
"""

import csv
import json
import shutil
from datetime import datetime, timedelta
from io import StringIO, BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from app.core.config import get_config
from app.core.singletons import LoggerSingleton, SQLiteSingleton
from app.answer.history import get_recent_history

_logger = LoggerSingleton().get()

router = APIRouter(prefix="/api/export", tags=["export"])


class ExportFormat(str, Enum):
    """Supported export formats."""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    HTML = "html"


class PDFExportRequest(BaseModel):
    """Request model for PDF export."""
    title: str
    content: str
    include_metadata: bool = True
    include_citations: bool = True
    custom_css: Optional[str] = None


class EntityExportFilters(BaseModel):
    """Filters for entity export."""
    entity_types: Optional[List[str]] = None
    confidence_threshold: float = 0.5
    source_documents: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class SummaryReportRequest(BaseModel):
    """Request model for summary report generation."""
    title: str = "SocioGraph Summary Report"
    date_range_days: int = 30
    include_analytics: bool = True
    include_top_entities: bool = True
    include_recent_queries: bool = True
    max_entities: int = 50


class AnalyticsReportRequest(BaseModel):
    """Request model for analytics report generation."""
    title: str = "SocioGraph Analytics Report"
    date_range_days: int = 30
    include_graphs: bool = True
    include_trends: bool = True
    document_ids: Optional[List[str]] = None


async def generate_report_pdf(content: str, title: str, output_path: str, metadata: Optional[Dict] = None, custom_css: Optional[str] = None):
    """Generate PDF report using existing PDF generation system."""
    from backend.app.answer.pdf import save_pdf
    
    # Use existing PDF generation with the content
    pdf_path = save_pdf(content, title)
    
    # Copy to specified path if different
    if str(pdf_path) != output_path:
        shutil.copy2(pdf_path, output_path)


@router.post("/pdf", response_class=FileResponse)
async def export_pdf(request: PDFExportRequest) -> FileResponse:
    """Generate and download PDF report."""
    try:
        cfg = get_config()
        cfg.SAVED_DIR.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"custom_report_{timestamp}.pdf"
        output_path = cfg.SAVED_DIR / filename
        
        await generate_report_pdf(
            content=request.content,
            title=request.title,
            output_path=str(output_path)
        )
        
        _logger.info(f"Generated custom PDF report: {filename}")
        
        return FileResponse(
            path=str(output_path),
            filename=filename,
            media_type="application/pdf"
        )
        
    except Exception as e:
        _logger.error(f"Failed to generate PDF report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.get("/history/{format}")
async def export_history(
    format: ExportFormat,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(1000, le=10000)
) -> StreamingResponse:
    """Export query history in various formats."""
    try:
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        history_data = get_recent_history(limit=limit)
        
        # Filter by date range
        filtered_history = []
        for record in history_data:
            try:
                record_date = datetime.fromisoformat(record.get("timestamp", ""))
                if start_date <= record_date <= end_date:
                    filtered_history.append(record)
            except:
                continue
        
        if format == ExportFormat.JSON:
            content = json.dumps(filtered_history, indent=2, default=str)
            media_type = "application/json"
            filename = f"history_export_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
            
        elif format == ExportFormat.CSV:
            output = StringIO()
            if filtered_history:
                fieldnames = filtered_history[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(filtered_history)
            content = output.getvalue()
            media_type = "text/csv"
            filename = f"history_export_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
        
        _logger.info(f"Exported {len(filtered_history)} history records in {format} format")
        
        return StreamingResponse(
            BytesIO(content.encode('utf-8')),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Failed to export history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"History export failed: {str(e)}")


@router.post("/entities/{format}")
async def export_entities(
    format: ExportFormat,
    filters: EntityExportFilters
) -> StreamingResponse:
    """Export entity data in specified format."""
    try:
        db_conn = SQLiteSingleton().get()
        
        # Build query with filters
        where_conditions = ["1=1"]
        params = []
        
        if filters.entity_types:
            placeholders = ",".join("?" * len(filters.entity_types))
            where_conditions.append(f"entity_type IN ({placeholders})")
            params.extend(filters.entity_types)
        
        if filters.confidence_threshold:
            where_conditions.append("confidence_score >= ?")
            params.append(filters.confidence_threshold)
        
        if filters.source_documents:
            placeholders = ",".join("?" * len(filters.source_documents))
            where_conditions.append(f"source_document IN ({placeholders})")
            params.extend(filters.source_documents)
        
        where_clause = " AND ".join(where_conditions)
        
        # Query entities
        query = f"""
            SELECT entity_id, entity_name, entity_type, description, 
                   confidence_score, source_document, created_at
            FROM entity 
            WHERE {where_clause}
            ORDER BY confidence_score DESC, entity_name
        """
        
        cursor = db_conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        
        # Convert to list of dictionaries
        entities = []
        for row in results:
            entities.append({
                "entity_id": row[0],
                "entity_name": row[1],
                "entity_type": row[2],
                "description": row[3],
                "confidence_score": row[4],
                "source_document": row[5],
                "created_at": row[6]
            })
        
        # Generate export based on format
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == ExportFormat.JSON:
            content = json.dumps(entities, indent=2, default=str)
            media_type = "application/json"
            filename = f"entities_export_{timestamp}.json"
            
        elif format == ExportFormat.CSV:
            output = StringIO()
            if entities:
                fieldnames = entities[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(entities)
            content = output.getvalue()
            media_type = "text/csv"
            filename = f"entities_export_{timestamp}.csv"
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
        
        _logger.info(f"Exported {len(entities)} entities in {format} format")
        
        return StreamingResponse(
            BytesIO(content.encode('utf-8')),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Failed to export entities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Entity export failed: {str(e)}")


def _generate_summary_report_content(data: Dict[str, Any]) -> str:
    """Generate markdown content for summary report."""
    content = f"""# {data['title']}

**Generated:** {data['generated_at']}  
**Date Range:** {data['date_range']['start']} to {data['date_range']['end']} ({data['date_range']['days']} days)

## System Overview

"""
    
    if "analytics" in data:
        analytics = data["analytics"]
        content += f"""### Statistics
- **Total Documents:** {analytics['total_documents']}
- **Total Entities:** {analytics['total_entities']}
- **Total Relationships:** {analytics['total_relationships']}

### Entity Type Distribution
"""
        for entity_type, count in analytics["entity_type_distribution"].items():
            content += f"- **{entity_type}:** {count}\n"
    
    if "top_entities" in data:
        content += "\n## Top Entities\n\n"
        for i, entity in enumerate(data["top_entities"][:10], 1):
            content += f"{i}. **{entity['name']}** ({entity['type']}) - {entity['relationships']} relationships\n"
    
    if "recent_activity" in data:
        content += "\n## Recent Activity\n\n"
        for activity in data["recent_activity"][:5]:
            content += f"- **{activity.get('timestamp', 'Unknown')}:** {activity.get('query', 'No query')}\n"
    
    return content


@router.post("/reports/summary")
async def generate_summary_report(request: SummaryReportRequest) -> FileResponse:
    """Generate comprehensive summary report."""
    try:
        cfg = get_config()
        db_conn = SQLiteSingleton().get()
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=request.date_range_days)
        
        # Gather summary data
        report_data = {
            "title": request.title,
            "generated_at": end_date.isoformat(),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": request.date_range_days
            }
        }
        
        # Get system statistics
        if request.include_analytics:
            cursor = db_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents")
            doc_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM entity")
            entity_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM relation")
            relation_count = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT entity_type, COUNT(*) 
                FROM entity 
                GROUP BY entity_type 
                ORDER BY COUNT(*) DESC
            """)
            entity_types = cursor.fetchall()
            cursor.close()
            
            report_data["analytics"] = {
                "total_documents": doc_count,
                "total_entities": entity_count,
                "total_relationships": relation_count,
                "entity_type_distribution": {row[0]: row[1] for row in entity_types}
            }
        
        # Get top entities
        if request.include_top_entities:
            cursor = db_conn.cursor()
            cursor.execute(f"""
                SELECT entity_name, entity_type, confidence_score, 
                       COUNT(r.relation_id) as relationship_count
                FROM entity e
                LEFT JOIN relation r ON (e.entity_id = r.subject_id OR e.entity_id = r.object_id)
                GROUP BY e.entity_id, e.entity_name, e.entity_type, e.confidence_score
                ORDER BY relationship_count DESC, confidence_score DESC
                LIMIT {request.max_entities}
            """)
            top_entities = cursor.fetchall()
            cursor.close()
            
            report_data["top_entities"] = [
                {
                    "name": row[0],
                    "type": row[1],
                    "confidence": row[2],
                    "relationships": row[3]
                }
                for row in top_entities
            ]
        
        # Get recent queries
        if request.include_recent_queries:
            recent_queries = get_recent_history(limit=10)
            report_data["recent_activity"] = recent_queries
        
        # Generate report content
        content = _generate_summary_report_content(report_data)
        
        # Generate PDF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"summary_report_{timestamp}.pdf"
        output_path = cfg.SAVED_DIR / filename
        
        await generate_report_pdf(
            content=content,
            title=request.title,
            output_path=str(output_path)
        )
        
        _logger.info(f"Generated summary report: {filename}")
        
        return FileResponse(
            path=str(output_path),
            filename=filename,
            media_type="application/pdf"
        )
        
    except Exception as e:
        _logger.error(f"Failed to generate summary report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Summary report generation failed: {str(e)}")
