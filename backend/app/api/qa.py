"""Q&A API endpoints for SocioGraph.

This module provides the FastAPI endpoints for question answering,
including streaming responses and PDF generation.
"""

import asyncio
import time
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel

from backend.app.core.singletons import LoggerSingleton
from backend.app.retriever import retrieve_context
from backend.app.answer.generator import generate_answer, generate_answer_complete
from backend.app.answer.pdf import save_pdf, get_pdf_url
from backend.app.answer.history import append_record, get_recent_history, get_history_stats

_logger = LoggerSingleton().get()

router = APIRouter(tags=["qa"])


class AskRequest(BaseModel):
    """Request model for asking questions."""
    query: str
    stream: bool = True  # Whether to stream the response


class AskResponse(BaseModel):
    """Response model for non-streaming ask requests."""
    answer: str
    pdf_url: str
    context_count: int
    token_count: int
    duration: float


@router.post("/ask")
async def ask_question(request: AskRequest) -> Any:
    """Ask a question and get a streaming or complete answer.
    
    This endpoint retrieves context for the query and generates an answer,
    optionally streaming the response in real-time.
    """
    start_time = time.time()
    query = request.query.strip()
    
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    _logger.info(f"Processing question: {query[:100]}...")
    
    try:
        # Retrieve context for the query
        _logger.info("Retrieving context...")
        context_result = retrieve_context(query)
        context_items = context_result.get("context", [])
        
        if not context_items:
            _logger.warning("No context retrieved for query")
            
        context_count = len(context_items)
        _logger.info(f"Retrieved {context_count} context items")
        
        if request.stream:
            # Return streaming response
            return EventSourceResponse(
                _stream_answer_events(query, context_items, start_time),
                media_type="text/plain"
            )
        else:
            # Return complete response
            return await _generate_complete_answer(query, context_items, start_time)
            
    except Exception as e:
        _logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


async def _stream_answer_events(query: str, context_items: list, start_time: float):
    """Generate Server-Sent Events for streaming answer."""
    complete_answer = ""
    token_count = 0
    
    try:
        # Send initial event
        yield {
            "event": "start", 
            "data": f"Starting answer generation for: {query[:100]}..."
        }
        
        # Stream answer tokens
        async for token in generate_answer(query, context_items):
            complete_answer += token
            token_count += 1
            
            # Send token event
            yield {
                "event": "token",
                "data": token
            }
            
        # Generate PDF after streaming completes
        try:
            pdf_path = save_pdf(complete_answer, query)
            pdf_url = get_pdf_url(pdf_path)
            
            # Send completion event
            duration = time.time() - start_time
            yield {
                "event": "complete",
                "data": f'{{"pdf_url": "{pdf_url}", "token_count": {token_count}, "duration": {duration:.2f}}}'
            }
            
            # Log to history
            append_record(
                query=query,
                pdf_path=pdf_path,
                token_count=token_count,
                context_count=len(context_items),
                duration=duration
            )
            
        except Exception as pdf_error:
            _logger.error(f"Error generating PDF: {pdf_error}")
            yield {
                "event": "error",
                "data": f"Answer generated but PDF creation failed: {str(pdf_error)}"
            }
            
    except Exception as e:
        _logger.error(f"Error in streaming: {e}")
        yield {
            "event": "error",
            "data": f"Error generating answer: {str(e)}"
        }


async def _generate_complete_answer(query: str, context_items: list, start_time: float) -> AskResponse:
    """Generate a complete (non-streaming) answer."""
    try:
        # Generate complete answer
        complete_answer = await generate_answer_complete(query, context_items)
        token_count = len(complete_answer.split())  # Rough token estimate
        
        # Generate PDF
        pdf_path = save_pdf(complete_answer, query)
        pdf_url = get_pdf_url(pdf_path)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log to history
        append_record(
            query=query,
            pdf_path=pdf_path,
            token_count=token_count,
            context_count=len(context_items),
            duration=duration
        )
        
        return AskResponse(
            answer=complete_answer,
            pdf_url=pdf_url,
            context_count=len(context_items),
            token_count=token_count,
            duration=duration
        )
        
    except Exception as e:
        _logger.error(f"Error generating complete answer: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")


@router.get("/history")
async def get_history(limit: int = 10) -> Dict[str, Any]:
    """Get recent query history.
    
    Args:
        limit: Maximum number of history records to return
    """
    try:
        history = get_recent_history(limit=limit)
        stats = get_history_stats()
        
        return {
            "history": history,
            "stats": stats
        }
        
    except Exception as e:
        _logger.error(f"Error retrieving history: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")


@router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """Get Q&A statistics."""
    try:
        stats = get_history_stats()
        return stats
        
    except Exception as e:
        _logger.error(f"Error retrieving stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")
