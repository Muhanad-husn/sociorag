"""WebSocket API endpoints for SocioGraph.

This module provides real-time communication functionality including:
- Real-time Q&A with streaming responses
- Document processing status updates
- System monitoring and notifications
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime


from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel

from app.core.singletons import LoggerSingleton
from app.retriever import retrieve_context
from app.answer.generator import generate_answer
from app.answer.history import append_record

_logger = LoggerSingleton().get()

router = APIRouter(prefix="/api/ws", tags=["websocket"])


class WebSocketMessage(BaseModel):
    """Base WebSocket message model."""
    type: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.now()


class QuestionMessage(BaseModel):
    """Question message for WebSocket Q&A."""
    type: str = "question"
    question: str
    session_id: Optional[str] = None


class ProcessingMessage(BaseModel):
    """Processing status message."""
    type: str = "processing_status"
    document_id: str
    status: str
    progress: float
    message: str


# Global connection management
class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.qa_connections: Dict[str, WebSocket] = {}  # session_id -> websocket
        self.processing_connections: Dict[str, List[WebSocket]] = {}  # document_id -> websockets
    
    async def connect(self, websocket: WebSocket, connection_type: str = "general", identifier: str = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if connection_type == "qa" and identifier:
            self.qa_connections[identifier] = websocket
        elif connection_type == "processing" and identifier:
            if identifier not in self.processing_connections:
                self.processing_connections[identifier] = []
            self.processing_connections[identifier].append(websocket)
        
        _logger.info(f"WebSocket connected: {connection_type} - {identifier}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Remove from specific connection types
        for session_id, ws in list(self.qa_connections.items()):
            if ws == websocket:
                del self.qa_connections[session_id]
                break
        
        for doc_id, ws_list in self.processing_connections.items():
            if websocket in ws_list:
                ws_list.remove(websocket)
                if not ws_list:  # Remove empty lists
                    del self.processing_connections[doc_id]
                break
        
        _logger.info("WebSocket disconnected")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            _logger.error(f"Failed to send WebSocket message: {str(e)}")
    
    async def send_json_message(self, data: Dict[str, Any], websocket: WebSocket):
        """Send JSON data to a specific WebSocket."""
        try:
            await websocket.send_json(data)
        except Exception as e:
            _logger.error(f"Failed to send WebSocket JSON: {str(e)}")
    
    async def broadcast_to_processing(self, document_id: str, message: Dict[str, Any]):
        """Broadcast a message to all connections monitoring a document."""
        if document_id in self.processing_connections:
            disconnected = []
            for websocket in self.processing_connections[document_id]:
                try:
                    await websocket.send_json(message)
                except:
                    disconnected.append(websocket)
            
            # Clean up disconnected websockets
            for ws in disconnected:
                if ws in self.processing_connections[document_id]:
                    self.processing_connections[document_id].remove(ws)


# Helper functions for connection management
async def send_periodic_heartbeat(websocket: WebSocket, interval: int = 30):
    """Send periodic heartbeats to keep the connection alive."""
    try:
        while True:
            await asyncio.sleep(interval)
            await websocket.send_json({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat()
            })
    except (asyncio.CancelledError, WebSocketDisconnect):
        # Task was cancelled or connection was closed
        pass
    except Exception as e:
        _logger.error(f"Error in heartbeat task: {str(e)}")


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/qa")
async def websocket_qa(websocket: WebSocket):
    """WebSocket endpoint for real-time Q&A.
    
    Provides streaming question-answering with real-time token generation.
    """
    session_id = None
    await manager.connect(websocket)
    heartbeat_task = None
    
    try:
        # Start a heartbeat task
        heartbeat_task = asyncio.create_task(send_periodic_heartbeat(websocket))
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            if data["type"] == "question":
                question = data.get("question", "").strip()
                session_id = data.get("session_id", f"ws_{datetime.now().timestamp()}")
                
                if not question:
                    await manager.send_json_message({
                        "type": "error",
                        "message": "Question cannot be empty"
                    }, websocket)
                    continue
                
                # Send acknowledgment
                await manager.send_json_message({
                    "type": "question_received",
                    "session_id": session_id,
                    "question": question
                }, websocket)
                
                try:
                    # Retrieve context
                    await manager.send_json_message({
                        "type": "status",
                        "message": "Retrieving context..."
                    }, websocket)
                    context = retrieve_context(question)
                    context_chunks = context.get("chunks", [])
                    
                    await manager.send_json_message({
                        "type": "status",
                        "message": "Generating answer...",
                        "context_chunks": len(context_chunks)
                    }, websocket)
                    
                    # Generate streaming answer
                    answer_tokens = []
                    # Stream the generated answer
                    async for token in generate_answer(question, context_chunks):
                        answer_tokens.append(token)
                        await manager.send_json_message({
                            "type": "token",
                            "content": token,
                            "session_id": session_id
                        }, websocket)
                    
                    # Send completion message
                    full_answer = "".join(answer_tokens)
                    await manager.send_json_message({
                        "type": "answer_complete",
                        "session_id": session_id,
                        "full_answer": full_answer,
                        "context_count": len(context_chunks),
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                    
                    # Save to history
                    append_record(
                        query=question,
                        token_count=len(answer_tokens),
                        context_count=len(context_chunks),
                        metadata={
                            "session_id": session_id,
                            "websocket": True,
                            "full_answer": full_answer
                        }
                    )
                    
                    _logger.info(f"WebSocket Q&A completed for session {session_id}")
                    
                except Exception as e:
                    await manager.send_json_message({
                        "type": "error",
                        "message": f"Failed to generate answer: {str(e)}",
                        "session_id": session_id
                    }, websocket)
                    _logger.error(f"WebSocket Q&A error: {str(e)}")
            
            elif data["type"] == "ping":
                # Respond to ping for connection health
                await manager.send_json_message({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
            
            else:
                await manager.send_json_message({
                    "type": "error",
                    "message": f"Unknown message type: {data['type']}"
                }, websocket)
                
    except WebSocketDisconnect:
        _logger.info(f"WebSocket Q&A client disconnected: {session_id}")
    except Exception as e:
        _logger.error(f"WebSocket Q&A error: {str(e)}")
    finally:
        # Cancel the heartbeat task
        if heartbeat_task is not None:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
        manager.disconnect(websocket)


@router.websocket("/processing/{document_id}")
async def websocket_processing_status(websocket: WebSocket, document_id: str):
    """WebSocket endpoint for real-time document processing status updates.
    
    Provides live updates on document processing progress.
    """
    await manager.connect(websocket, "processing", document_id)
    heartbeat_task = None
    
    try:
        # Start a heartbeat task
        heartbeat_task = asyncio.create_task(send_periodic_heartbeat(websocket))
        
        # Send initial status
        await manager.send_json_message({
            "type": "connected",
            "document_id": document_id,
            "message": "Connected to processing status updates",
            "timestamp": datetime.now().isoformat()
        }, websocket)
        
        # Keep connection alive and listen for client messages
        while True:
            try:
                # Wait for client messages or timeout after 30 seconds
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
                
                if data["type"] == "ping":
                    await manager.send_json_message({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                elif data["type"] == "get_status":
                    # Send current status (this would query actual processing status)
                    await manager.send_json_message({
                        "type": "status_update",
                        "document_id": document_id,
                        "status": "checking",
                        "progress": 0.0,
                        "message": "Checking processing status...",
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                    
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                await manager.send_json_message({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        _logger.info(f"WebSocket processing client disconnected: {document_id}")
    except Exception as e:
        _logger.error(f"WebSocket processing error: {str(e)}")
    finally:
        # Cancel the heartbeat task
        if heartbeat_task is not None:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
        manager.disconnect(websocket)


@router.websocket("/monitor")
async def websocket_system_monitor(websocket: WebSocket):
    """WebSocket endpoint for system monitoring and notifications.
    
    Provides real-time system status updates and notifications.
    """
    await manager.connect(websocket, "monitor")
    heartbeat_task = None
    
    try:
        # Start a heartbeat task
        heartbeat_task = asyncio.create_task(send_periodic_heartbeat(websocket))
        
        # Send initial connection message
        await manager.send_json_message({
            "type": "monitor_connected",
            "message": "Connected to system monitoring",
            "timestamp": datetime.now().isoformat()
        }, websocket)
        
        # Main monitoring loop
        while True:
            try:
                # Wait for client messages or timeout for periodic updates
                data = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)
                
                if data["type"] == "get_status":
                    # Send system status
                    await manager.send_json_message({
                        "type": "system_status",
                        "status": "operational",
                        "active_connections": len(manager.active_connections),
                        "qa_sessions": len(manager.qa_connections),
                        "processing_monitors": len(manager.processing_connections),
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                
                elif data["type"] == "ping":
                    await manager.send_json_message({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                    
            except asyncio.TimeoutError:
                # Send periodic status update
                await manager.send_json_message({
                    "type": "periodic_update",
                    "active_connections": len(manager.active_connections),
                    "timestamp": datetime.now().isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        _logger.info("WebSocket monitor client disconnected")
    except Exception as e:
        _logger.error(f"WebSocket monitor error: {str(e)}")
    finally:
        # Cancel the heartbeat task
        if heartbeat_task is not None:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
        manager.disconnect(websocket)


# Helper functions for broadcasting updates
async def broadcast_processing_update(document_id: str, status: str, progress: float, message: str):
    """Broadcast processing status update to all monitoring clients."""
    update_message = {
        "type": "processing_update",
        "document_id": document_id,
        "status": status,
        "progress": progress,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    await manager.broadcast_to_processing(document_id, update_message)
