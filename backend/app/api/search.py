"""Search API endpoints for SocioGraph.

This module provides comprehensive search functionality including:
- Entity search and discovery
- Relationship search and graph traversal
- Semantic search across documents
- Similar document discovery
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from app.core.singletons import LoggerSingleton, SQLiteSingleton, EmbeddingSingleton
from app.core.config import get_config

_logger = LoggerSingleton().get()

router = APIRouter(prefix="/api/search", tags=["search"])


# Request/Response Models
class EntitySearchResults(BaseModel):
    """Entity search results model."""
    entities: List[Dict[str, Any]]
    total: int
    query: str
    confidence_threshold: float


class RelationshipSearchResults(BaseModel):
    """Relationship search results model."""
    relationships: List[Dict[str, Any]]
    total: int
    filters: Dict[str, Any]


class RelationshipList(BaseModel):
    """List of relationships for an entity."""
    entity_id: str
    relationships: List[Dict[str, Any]]
    total: int
    depth: int


class SemanticSearchRequest(BaseModel):
    """Request model for semantic search."""
    query: str
    limit: int = 20
    confidence_threshold: float = 0.7
    include_entities: bool = True
    include_chunks: bool = True


class SemanticSearchResults(BaseModel):
    """Semantic search results model."""
    query: str
    chunks: List[Dict[str, Any]]
    entities: List[Dict[str, Any]]
    total_chunks: int
    total_entities: int
    confidence_threshold: float


class SimilarDocumentsList(BaseModel):
    """List of similar documents."""
    document_id: str
    similar_documents: List[Dict[str, Any]]
    total: int


@router.get("/entities", response_model=EntitySearchResults)
async def search_entities(
    q: str = Query(..., min_length=1, description="Search query for entities"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    confidence_threshold: float = Query(0.5, ge=0.0, le=1.0, description="Minimum confidence score"),
    limit: int = Query(20, le=100, description="Maximum number of results")
) -> EntitySearchResults:
    """Search for entities in the knowledge base.
    
    This endpoint performs semantic search over entity names and descriptions
    to find relevant entities matching the query.
    """
    try:
        db_conn = SQLiteSingleton().get()
        embedding_service = EmbeddingSingleton()
        
        # Get query embedding
        query_embedding = embedding_service.embed([q])[0]
        
        # Build SQL query with optional type filter
        where_conditions = ["1=1"]  # Base condition
        params = []
        
        if entity_type:
            where_conditions.append("entity_type = ?")
            params.append(entity_type)
        
        where_clause = " AND ".join(where_conditions)
        
        # Search entities using vector similarity
        # Note: This is a simplified version - you may need to implement vector search
        # based on your SQLite-vec setup
        query = f"""
            SELECT entity_id, entity_name, entity_type, description, 
                   confidence_score, source_document, created_at
            FROM entity 
            WHERE {where_clause}
            AND entity_name LIKE ?
            ORDER BY confidence_score DESC
            LIMIT ?
        """
        
        # Add LIKE parameter for text search fallback
        params.extend([f"%{q}%", limit])
        
        cursor = db_conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        
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
        
        # Filter by confidence threshold
        filtered_entities = [
            e for e in entities 
            if e["confidence_score"] >= confidence_threshold
        ]
        
        _logger.info(f"Entity search for '{q}' returned {len(filtered_entities)} results")
        
        return EntitySearchResults(
            entities=filtered_entities,
            total=len(filtered_entities),
            query=q,
            confidence_threshold=confidence_threshold
        )
        
    except Exception as e:
        _logger.error(f"Entity search failed for query '{q}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/entities/{entity_id}/relationships")
async def get_entity_relationships(
    entity_id: str,
    relationship_type: Optional[str] = Query(None, description="Filter by relationship type"),
    depth: int = Query(1, ge=1, le=3, description="Relationship traversal depth")
) -> RelationshipList:
    """Get relationships for a specific entity.
    
    This endpoint returns all relationships connected to the specified entity,
    with optional filtering by relationship type and traversal depth.
    """
    try:
        db_conn = SQLiteSingleton().get()
        
        # Verify entity exists
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT entity_name FROM entity WHERE entity_id = ?
        """, (entity_id,))
        entity_check = cursor.fetchall()
        cursor.close()
        
        if not entity_check:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        # Build relationship query
        where_conditions = ["(r.subject_id = ? OR r.object_id = ?)"]
        params = [entity_id, entity_id]
        
        if relationship_type:
            where_conditions.append("r.relation_type = ?")
            params.append(relationship_type)
        
        where_clause = " AND ".join(where_conditions)
        
        # Query relationships with entity details
        query = f"""
            SELECT r.relation_id, r.subject_id, r.relation_type, r.object_id,
                   r.confidence_score, r.source_document,
                   e1.entity_name as subject_name, e1.entity_type as subject_type,
                   e2.entity_name as object_name, e2.entity_type as object_type
            FROM relation r
            JOIN entity e1 ON r.subject_id = e1.entity_id
            JOIN entity e2 ON r.object_id = e2.entity_id
            WHERE {where_clause}
            ORDER BY r.confidence_score DESC
        """
        
        cursor = db_conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        
        relationships = []
        for row in results:
            relationships.append({
                "relation_id": row[0],
                "subject": {
                    "entity_id": row[1],
                    "entity_name": row[6],
                    "entity_type": row[7]
                },
                "relation_type": row[2],
                "object": {
                    "entity_id": row[3],
                    "entity_name": row[8],
                    "entity_type": row[9]
                },
                "confidence_score": row[4],
                "source_document": row[5]
            })
        
        _logger.info(f"Found {len(relationships)} relationships for entity {entity_id}")
        
        return RelationshipList(
            entity_id=entity_id,
            relationships=relationships,
            total=len(relationships),
            depth=depth
        )
        
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Failed to get relationships for entity {entity_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get relationships: {str(e)}")


@router.get("/relationships", response_model=RelationshipSearchResults)
async def search_relationships(
    entity1: Optional[str] = Query(None, description="First entity name or ID"),
    entity2: Optional[str] = Query(None, description="Second entity name or ID"),
    relationship_type: Optional[str] = Query(None, description="Relationship type filter"),
    confidence_threshold: float = Query(0.5, ge=0.0, le=1.0, description="Minimum confidence score")
) -> RelationshipSearchResults:
    """Search for relationships between entities.
    
    This endpoint allows searching for relationships with various filters
    including entity names/IDs and relationship types.
    """
    try:
        db_conn = SQLiteSingleton().get()
        
        # Build dynamic query based on provided filters
        where_conditions = []
        params = []
        
        if entity1:
            where_conditions.append("""
                (e1.entity_name LIKE ? OR e1.entity_id = ? OR 
                 e2.entity_name LIKE ? OR e2.entity_id = ?)
            """)
            params.extend([f"%{entity1}%", entity1, f"%{entity1}%", entity1])
        
        if entity2:
            where_conditions.append("""
                (e1.entity_name LIKE ? OR e1.entity_id = ? OR 
                 e2.entity_name LIKE ? OR e2.entity_id = ?)
            """)
            params.extend([f"%{entity2}%", entity2, f"%{entity2}%", entity2])
        
        if relationship_type:
            where_conditions.append("r.relation_type = ?")
            params.append(relationship_type)
        
        where_conditions.append("r.confidence_score >= ?")
        params.append(confidence_threshold)
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Query relationships
        query = f"""
            SELECT r.relation_id, r.subject_id, r.relation_type, r.object_id,
                   r.confidence_score, r.source_document,
                   e1.entity_name as subject_name, e1.entity_type as subject_type,
                   e2.entity_name as object_name, e2.entity_type as object_type
            FROM relation r
            JOIN entity e1 ON r.subject_id = e1.entity_id
            JOIN entity e2 ON r.object_id = e2.entity_id
            WHERE {where_clause}
            ORDER BY r.confidence_score DESC
            LIMIT 100
        """
        
        cursor = db_conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        
        relationships = []
        for row in results:
            relationships.append({
                "relation_id": row[0],
                "subject": {
                    "entity_id": row[1],
                    "entity_name": row[6],
                    "entity_type": row[7]
                },
                "relation_type": row[2],
                "object": {
                    "entity_id": row[3],
                    "entity_name": row[8],
                    "entity_type": row[9]
                },
                "confidence_score": row[4],
                "source_document": row[5]
            })
        
        filters = {
            "entity1": entity1,
            "entity2": entity2,
            "relationship_type": relationship_type,
            "confidence_threshold": confidence_threshold
        }
        
        _logger.info(f"Relationship search returned {len(relationships)} results")
        
        return RelationshipSearchResults(
            relationships=relationships,
            total=len(relationships),
            filters=filters
        )
        
    except Exception as e:
        _logger.error(f"Relationship search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/relationships/types")
async def get_relationship_types() -> List[str]:
    """Get all available relationship types in the knowledge base."""
    try:
        db_conn = SQLiteSingleton().get()
        
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT DISTINCT relation_type 
            FROM relation 
            ORDER BY relation_type
        """)
        results = cursor.fetchall()
        cursor.close()
        
        relationship_types = [row[0] for row in results]
        
        _logger.info(f"Found {len(relationship_types)} unique relationship types")
        
        return relationship_types
        
    except Exception as e:
        _logger.error(f"Failed to get relationship types: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get relationship types: {str(e)}")


@router.post("/semantic", response_model=SemanticSearchResults)
async def semantic_search(request: SemanticSearchRequest) -> SemanticSearchResults:
    """Perform semantic search across documents.
    
    This endpoint performs semantic search using embeddings to find
    relevant chunks and entities based on the query.
    """
    try:
        from backend.app.retriever import retrieve_context
        
        # Use existing retrieval system for semantic search
        context = retrieve_context(request.query)
        
        chunks = []
        entities = []
        
        # Process chunks if requested
        if request.include_chunks and "chunks" in context:
            for chunk in context["chunks"][:request.limit]:
                chunks.append({
                    "chunk_id": chunk.get("id", "unknown"),
                    "content": chunk.get("content", ""),
                    "similarity_score": chunk.get("score", 0.0),
                    "source_document": chunk.get("source", "unknown"),
                    "page_number": chunk.get("page", None)
                })
        
        # Process entities if requested
        if request.include_entities and "entities" in context:
            for entity in context["entities"][:request.limit]:
                entities.append({
                    "entity_id": entity.get("id", "unknown"),
                    "entity_name": entity.get("name", ""),
                    "entity_type": entity.get("type", "unknown"),
                    "similarity_score": entity.get("score", 0.0),
                    "description": entity.get("description", "")
                })
        
        _logger.info(f"Semantic search for '{request.query}' returned {len(chunks)} chunks and {len(entities)} entities")
        
        return SemanticSearchResults(
            query=request.query,
            chunks=chunks,
            entities=entities,
            total_chunks=len(chunks),
            total_entities=len(entities),
            confidence_threshold=request.confidence_threshold
        )
        
    except Exception as e:
        _logger.error(f"Semantic search failed for query '{request.query}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")


@router.get("/similar/{document_id}")
async def find_similar_documents(
    document_id: str,
    limit: int = Query(10, le=50, description="Maximum number of similar documents")
) -> SimilarDocumentsList:
    """Find documents similar to the given document.
    
    This endpoint uses document embeddings to find semantically similar documents.
    """
    try:
        db_conn = SQLiteSingleton().get()
        
        # Verify document exists
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT original_filename FROM documents WHERE document_id = ?
        """, (document_id,))
        doc_check = cursor.fetchall()
        cursor.close()
        
        if not doc_check:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # For now, implement a simple similarity based on entity overlap
        # In a full implementation, you would use document embeddings
        query = """
            SELECT d.document_id, d.original_filename, d.upload_time,
                   COUNT(DISTINCT e.entity_name) as shared_entities
            FROM documents d
            JOIN entity e1 ON e1.source_document = ?
            JOIN entity e2 ON e2.source_document = d.document_id 
                         AND e2.entity_name = e1.entity_name
            WHERE d.document_id != ?
            GROUP BY d.document_id, d.original_filename, d.upload_time
            ORDER BY shared_entities DESC
            LIMIT ?
        """
        
        cursor = db_conn.cursor()
        cursor.execute(query, (document_id, document_id, limit))
        results = cursor.fetchall()
        cursor.close()
        
        similar_docs = []
        for row in results:
            similar_docs.append({
                "document_id": row[0],
                "filename": row[1],
                "upload_time": row[2],
                "similarity_score": row[3] / 100.0,  # Normalize shared entities
                "shared_entities": row[3]
            })
        
        _logger.info(f"Found {len(similar_docs)} similar documents for {document_id}")
        
        return SimilarDocumentsList(
            document_id=document_id,
            similar_documents=similar_docs,
            total=len(similar_docs)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Failed to find similar documents for {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to find similar documents: {str(e)}")
