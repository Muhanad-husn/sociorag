"""Process state management for SocioGraph.

This module manages the state of long-running processes like document ingestion
to prevent multiple simultaneous processes and provide accurate progress tracking.
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, AsyncGenerator, Generator
from dataclasses import dataclass, asdict
from enum import Enum
import threading

from backend.app.core.singletons import LoggerSingleton

logger = LoggerSingleton().get()


class ProcessStatus(Enum):
    """Status of a process."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ProcessState:
    """State of a process."""
    status: ProcessStatus = ProcessStatus.IDLE
    progress: int = 0
    phase: str = ""
    message: str = ""
    current_file: str = ""
    files_processed: int = 0
    total_files: int = 0
    chunks_processed: int = 0
    total_chunks: int = 0
    entities_extracted: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['status'] = self.status.value
        return result


class ProcessStateManager:
    """Manages the state of long-running processes."""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._states: Dict[str, ProcessState] = {}
        self._active_generators: Dict[str, Generator] = {}
    
    def get_state(self, process_id: str) -> ProcessState:
        """Get the current state of a process."""
        with self._lock:
            return self._states.get(process_id, ProcessState())
    
    def set_state(self, process_id: str, state: ProcessState) -> None:
        """Set the state of a process."""
        with self._lock:
            self._states[process_id] = state
            logger.info(f"Process {process_id} state updated: {state.status.value} - {state.message}")
    
    def update_state(self, process_id: str, **kwargs) -> None:
        """Update specific fields of a process state."""
        with self._lock:
            current_state = self._states.get(process_id, ProcessState())
            for key, value in kwargs.items():
                if hasattr(current_state, key):
                    setattr(current_state, key, value)
            self._states[process_id] = current_state
    
    def is_running(self, process_id: str) -> bool:
        """Check if a process is currently running."""
        with self._lock:
            state = self._states.get(process_id, ProcessState())
            return state.status == ProcessStatus.RUNNING
    
    def start_process(self, process_id: str) -> bool:
        """Start a process if not already running."""
        with self._lock:
            if self.is_running(process_id):
                logger.warning(f"Process {process_id} is already running")
                return False
            
            state = ProcessState(
                status=ProcessStatus.RUNNING,
                start_time=time.time(),
                message="Process started"
            )
            self._states[process_id] = state
            logger.info(f"Started process {process_id}")
            return True
    
    def complete_process(self, process_id: str, success: bool = True, error_message: str = "") -> None:
        """Mark a process as completed."""
        with self._lock:
            current_state = self._states.get(process_id, ProcessState())
            current_state.status = ProcessStatus.COMPLETED if success else ProcessStatus.ERROR
            current_state.end_time = time.time()
            current_state.progress = 100 if success else current_state.progress
            current_state.error_message = error_message
            current_state.message = "Process completed successfully" if success else f"Process failed: {error_message}"
            self._states[process_id] = current_state
            
            # Clean up active generator
            if process_id in self._active_generators:
                del self._active_generators[process_id]
            
            logger.info(f"Process {process_id} completed with status: {current_state.status.value}")
    
    def set_active_generator(self, process_id: str, generator: Generator) -> None:
        """Set the active generator for a process."""
        with self._lock:
            self._active_generators[process_id] = generator
    
    def get_active_generator(self, process_id: str) -> Optional[Generator]:
        """Get the active generator for a process."""
        with self._lock:
            return self._active_generators.get(process_id)
    
    def reset_process(self, process_id: str) -> None:
        """Reset a process to idle state."""
        with self._lock:
            if process_id in self._states:
                del self._states[process_id]
            if process_id in self._active_generators:
                del self._active_generators[process_id]
            logger.info(f"Reset process {process_id}")


# Global instance
_process_manager = ProcessStateManager()


def get_process_manager() -> ProcessStateManager:
    """Get the global process state manager."""
    return _process_manager
