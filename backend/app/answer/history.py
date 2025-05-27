"""History logging for Q&A sessions.

This module handles logging of queries, answers, and metadata for later review.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.config import get_config
from app.core.singletons import LoggerSingleton

_cfg = get_config()
_logger = LoggerSingleton().get()


def _ensure_saved_dir() -> Path:
    """Ensure the saved directory exists."""
    saved_dir = _cfg.SAVED_DIR
    saved_dir.mkdir(parents=True, exist_ok=True)
    return saved_dir


def _get_history_file() -> Path:
    """Get the path to the history JSONL file."""
    saved_dir = _ensure_saved_dir()
    return saved_dir / "history.jsonl"


def append_record(
    query: str, 
    pdf_path: Optional[Path] = None, 
    token_count: int = 0,
    context_count: int = 0,
    duration: float = 0.0,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Append a Q&A record to the history log.
    
    Args:
        query: The user's question
        pdf_path: Path to the generated PDF (if any)
        token_count: Number of tokens generated
        context_count: Number of context items used
        duration: Time taken to generate the answer (seconds)
        metadata: Additional metadata to store
    """
    try:
        history_file = _get_history_file()
        
        # Build the record
        record = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "query": query,
            "pdf_path": str(pdf_path) if pdf_path else None,
            "pdf_filename": pdf_path.name if pdf_path else None,
            "token_count": token_count,
            "context_count": context_count,
            "duration_seconds": round(duration, 2),
            "metadata": metadata or {}
        }
        
        # Append to JSONL file
        with open(history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            
        _logger.info(f"Appended history record for query: {query[:100]}...")
        
    except Exception as e:
        _logger.error(f"Error appending history record: {e}")
        # Don't raise - history logging shouldn't break the main flow


def get_recent_history(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get recent history records.
    
    Args:
        limit: Maximum number of records to return (None for all)
        
    Returns:
        List of history records, newest first
    """
    try:
        history_file = _get_history_file()
        
        if not history_file.exists():
            return []
            
        records = []
        with open(history_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        record = json.loads(line)
                        records.append(record)
                    except json.JSONDecodeError as e:
                        _logger.warning(f"Skipping malformed history line: {e}")
                        continue
        
        # Sort by timestamp (newest first) and apply limit
        records.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        if limit is not None:
            records = records[:limit]
            
        return records
        
    except Exception as e:
        _logger.error(f"Error reading history: {e}")
        return []


def get_history_stats() -> Dict[str, Any]:
    """Get statistics about the query history.
    
    Returns:
        Dictionary with history statistics
    """
    try:
        records = get_recent_history()
        
        if not records:
            return {
                "total_queries": 0,
                "total_tokens": 0,
                "avg_duration": 0.0,
                "last_query_time": None
            }
        
        total_queries = len(records)
        total_tokens = sum(r.get("token_count", 0) for r in records)
        durations = [r.get("duration_seconds", 0) for r in records if r.get("duration_seconds", 0) > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        last_query_time = records[0].get("datetime") if records else None
        
        return {
            "total_queries": total_queries,
            "total_tokens": total_tokens,
            "avg_duration": round(avg_duration, 2),
            "last_query_time": last_query_time
        }
        
    except Exception as e:
        _logger.error(f"Error calculating history stats: {e}")
        return {
            "total_queries": 0,
            "total_tokens": 0,
            "avg_duration": 0.0,
            "last_query_time": None
        }


def cleanup_old_history(max_records: Optional[int] = None) -> int:
    """Remove old history records, keeping only the most recent ones.
    
    Args:
        max_records: Maximum number of records to keep (uses config default if None)
        
    Returns:
        Number of records removed
    """
    if max_records is None:
        max_records = _cfg.HISTORY_LIMIT
        
    try:
        records = get_recent_history()
        
        if len(records) <= max_records:
            return 0  # Nothing to clean up
            
        # Keep only the most recent records
        records_to_keep = records[:max_records]
        removed_count = len(records) - len(records_to_keep)
        
        # Rewrite the history file
        history_file = _get_history_file()
        with open(history_file, "w", encoding="utf-8") as f:
            for record in records_to_keep:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                
        _logger.info(f"Cleaned up {removed_count} old history records")
        return removed_count
        
    except Exception as e:
        _logger.error(f"Error cleaning up history: {e}")
        return 0
