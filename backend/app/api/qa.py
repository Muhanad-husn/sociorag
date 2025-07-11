"""Q&A API endpoints for SocioGraph.

This module provides the FastAPI endpoints for question answering
and PDF generation.
"""

import asyncio
import time
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.app.core.singletons import LoggerSingleton
from backend.app.retriever import retrieve_context
from backend.app.answer.generator import generate_answer, generate_answer_complete

from backend.app.answer.history import append_record, get_recent_history, get_history_stats
from backend.app.answer.prompt import extract_title_and_content, sanitize_filename
from backend.app.answer.markdown_renderer import render_markdown_to_html_safe_cached

_logger = LoggerSingleton().get()

router = APIRouter(prefix="/api/qa", tags=["qa"])


class AskRequest(BaseModel):
    """Request model for asking questions."""
    query: str
    translate_to_arabic: Optional[bool] = False
    answer_model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    context_window: Optional[int] = None
    top_k: Optional[int] = None  # Number of vector results to retrieve
    top_k_rerank: Optional[int] = None  # Number of results to keep after reranking


class AskResponse(BaseModel):
    """Response model for non-streaming ask requests."""
    answer: str
    answer_html: str  # Pre-rendered HTML for frontend consumption
    context_count: int
    token_count: int
    duration: float
    language: str = "en"  # Default language is English


@router.post("/ask")
async def ask_question(request: AskRequest) -> AskResponse:
    """Ask a question and get a complete answer.
    
    This endpoint retrieves context for the query and generates an answer.
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
        
        # Generate complete response
        return await _generate_complete_answer(query, context_items, start_time, request)
            
    except Exception as e:
        _logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


async def _generate_complete_answer(query: str, context_items: list, start_time: float, request: AskRequest) -> AskResponse:
    """Generate a complete (non-streaming) answer."""
    try:
        # Generate complete answer with parameters from request
        model = request.answer_model
        temperature = request.temperature
        max_tokens = request.max_tokens
        context_window = request.context_window
        translate_to_arabic = request.translate_to_arabic
        
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
        
        # Default language is English
        language = "en"
        
        # Translate to Arabic if requested
        if translate_to_arabic:
            try:
                from backend.app.retriever.language import translate_with_llm
                _logger.info("Translating answer to Arabic")
                complete_answer = await translate_with_llm(complete_answer, "en", "ar")
                language = "ar"
                _logger.info("Translation completed")
            except Exception as e:
                _logger.error(f"Translation error: {e}")                # Continue with English answer if translation fails
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log to history
        append_record(
            query=query,
            pdf_path=None,
            token_count=token_count,
            context_count=len(context_items),
            duration=duration
        )
        
        # Convert markdown to HTML for frontend consumption with sanitization and caching
        answer_html = render_markdown_to_html_safe_cached(complete_answer)
        
        return AskResponse(
            answer=complete_answer,
            answer_html=answer_html,
            context_count=len(context_items),
            token_count=token_count,
            duration=duration,
            language=language
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        _logger.error(f"Error generating complete answer: {e}")
        _logger.error(f"Full traceback: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)} | Type: {type(e)} | Details: {error_details[:200]}")


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
) -> AskResponse:
    """Ask a question via GET method with query parameters.
    
    This endpoint provides compatibility for GET requests.
    """
    request = AskRequest(
        query=query,
        translate_to_arabic=translate_to_arabic,
        answer_model=answer_model,
        temperature=temperature,
        max_tokens=max_tokens,
        context_window=context_window,
        top_k=top_k,
        top_k_rerank=top_k_r
    )
    return await ask_question(request)
