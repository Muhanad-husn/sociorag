"""Q&A API endpoints for SocioGraph.

This module provides the FastAPI endpoints for question answering,
including streaming responses and PDF generation.
"""

import asyncio
import time
from typing import Dict, Any, Optional

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

router = APIRouter(prefix="/api/qa", tags=["qa"])


class AskRequest(BaseModel):
    """Request model for asking questions."""
    query: str
    stream: bool = True  # Whether to stream the response
    answer_model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    context_window: Optional[int] = None
    top_k: Optional[int] = None  # Number of vector results to retrieve
    top_k_rerank: Optional[int] = None  # Number of results to keep after reranking


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
        # Pass optional top_k parameters if provided in the request
        retrieval_params = {}
        if request.top_k is not None:
            retrieval_params['top_k'] = request.top_k
        if request.top_k_rerank is not None:
            retrieval_params['top_k_rerank'] = request.top_k_rerank
            
        context_result = retrieve_context(query, **retrieval_params)
        context_data = context_result.get("context", {})
        context_items = context_data.get("merged_texts", [])
        
        if not context_items:
            _logger.warning("No context retrieved for query")
            
        context_count = len(context_items)
        _logger.info(f"Retrieved {context_count} context items")
        if request.stream:
            # Return streaming response
            return EventSourceResponse(
                _stream_answer_events(query, context_items, start_time, request),
                media_type="text/plain"
            )
        else:
            # Return complete response
            return await _generate_complete_answer(query, context_items, start_time, request)
            
    except Exception as e:
        _logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


async def _stream_answer_events(query: str, context_items: list, start_time: float, request: AskRequest):
    """Generate Server-Sent Events for streaming answer."""
    complete_answer = ""
    token_count = 0
    
    try:
        # Send initial event
        yield {
            "event": "start", 
            "data": f"Starting answer generation for: {query[:100]}..."
        }
        
        # Get the LLM parameters
        model = request.answer_model
        temperature = request.temperature
        max_tokens = request.max_tokens
        context_window = request.context_window
        
        # Stream answer tokens
        async for token in generate_answer(
            query, 
            context_items, 
            model=model, 
            temperature=temperature, 
            max_tokens=max_tokens, 
            context_window=context_window
        ):
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


async def _generate_complete_answer(query: str, context_items: list, start_time: float, request: AskRequest) -> AskResponse:
    """Generate a complete (non-streaming) answer."""
    try:
        # Generate complete answer with parameters from request
        model = request.answer_model
        temperature = request.temperature
        max_tokens = request.max_tokens
        context_window = request.context_window
        
        # Get parameters from the request for LLM
        llm_params = {}
        if model:
            llm_params["model"] = model
        if temperature:
            llm_params["temperature"] = temperature
        if max_tokens:
            llm_params["max_tokens"] = max_tokens
        if context_window:
            llm_params["context_window"] = context_window
        
        # Generate answer with parameters
        complete_answer = ""
        async for token in generate_answer(query, context_items, **llm_params):
            complete_answer += token
            
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


@router.get("/ask")
async def ask_question_get(
    query: str,
    translate_to_arabic: bool = False,
    top_k: int = 5,
    top_k_r: int = 3,
    temperature: float = 0.7,
    answer_model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    context_window: Optional[int] = None
) -> Any:
    """Ask a question via GET method with query parameters.
    
    This endpoint is primarily for compatibility with SSE streaming from the frontend.
    """
    request = AskRequest(
        query=query,
        stream=True,
        answer_model=answer_model,
        temperature=temperature,
        max_tokens=max_tokens,
        context_window=context_window,
        top_k=top_k,
        top_k_rerank=top_k_r
    )
    return await ask_question(request)
