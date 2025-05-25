# filepath: d:\sociorag\backend\app\core\singletons.py
"""Infrastructure Singletons for SocioGraph.

This module provides lazy-loaded, thread-safe singletons for all heavy infrastructure:
- LoggerSingleton: Centralized logging
- EmbeddingSingleton: Sentence transformer model
- ChromaSingleton: Persistent vector store
- SQLiteSingleton: Graph database with sqlite-vec
- LLMClientSingleton: OpenRouter client wrapper
- NLPSingleton: spaCy pipeline
"""

import logging
import sqlite3
import threading
from typing import Any, AsyncGenerator, Dict, List, Optional, Union
from pathlib import Path
import os

import spacy
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings

from .config import get_config


class _SingletonMeta(type):
    """Thread-safe singleton metaclass."""
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class LoggerSingleton(metaclass=_SingletonMeta):
    """Singleton logger instance."""
    
    def __init__(self):
        self._logger = None
        
    def get(self) -> logging.Logger:
        """Get the singleton logger instance."""
        if self._logger is None:
            config = get_config()
            self._logger = logging.getLogger("sociograph")
            
            # Set level from config
            level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
            self._logger.setLevel(level)
            
            # Add console handler if none exists
            if not self._logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                self._logger.addHandler(handler)
                
        return self._logger


class EmbeddingSingleton(metaclass=_SingletonMeta):
    """Singleton sentence transformer model."""
    
    def __init__(self):
        self._model = None
        
    def get(self) -> SentenceTransformer:
        """Get the singleton embedding model."""
        if self._model is None:
            config = get_config()
            logger = LoggerSingleton().get()
            logger.info(f"Loading embedding model: {config.EMBEDDING_MODEL}")
            self._model = SentenceTransformer(config.EMBEDDING_MODEL)
            
        return self._model
    
    def embed(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Embed text(s) and return embeddings."""
        model = self.get()
        embeddings = model.encode(texts)
        
        if isinstance(texts, str):
            return embeddings.tolist()
        else:
            return [emb.tolist() for emb in embeddings]


class ChromaSingleton(metaclass=_SingletonMeta):
    """Singleton Chroma vector store."""
    
    def __init__(self):
        self._chroma = None
        
    def get(self) -> Chroma:
        """Get the singleton Chroma instance."""
        if self._chroma is None:
            config = get_config()
            logger = LoggerSingleton().get()
            
            # Ensure vector directory exists
            config.VECTOR_DIR.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Initializing Chroma at: {config.VECTOR_DIR}")
            
            # Create embedding function wrapper
            embedding_function = SentenceTransformerEmbeddings(
                model_name=config.EMBEDDING_MODEL
            )
            
            self._chroma = Chroma(
                persist_directory=str(config.VECTOR_DIR),
                embedding_function=embedding_function,
                collection_name="documents"
            )
            
        return self._chroma


class SQLiteSingleton(metaclass=_SingletonMeta):
    """Singleton SQLite connection with sqlite-vec extension."""
    
    def __init__(self):
        self._connection = None
        
    def get(self) -> sqlite3.Connection:
        """Get the singleton SQLite connection."""
        if self._connection is None:
            config = get_config()
            logger = LoggerSingleton().get()
            
            # Ensure parent directory exists
            config.GRAPH_DB.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Connecting to SQLite database: {config.GRAPH_DB}")
            
            self._connection = sqlite3.connect(
                str(config.GRAPH_DB),
                check_same_thread=False,
                timeout=30.0
            )
            
            # Enable WAL mode for better concurrency
            self._connection.execute("PRAGMA journal_mode=WAL")
            
            # Try to load sqlite-vec extension
            try:
                self._connection.enable_load_extension(True)
                self._connection.load_extension("vec0")
                logger.info("Loaded sqlite-vec extension")
            except Exception as e:
                logger.warning(f"Could not load sqlite-vec extension: {e}")
                # Continue without vector extension for now
            
            # Create tables if they don't exist
            self._create_tables()
            
        return self._connection
    
    def _create_tables(self):
        """Create entity and relation tables if they don't exist."""
        # Ensure connection is established
        if self._connection is None:
            return
            
        cursor = self._connection.cursor()
        
        # Check if tables exist and their structure
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='entity'")
        entity_exists = cursor.fetchone() is not None
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='relation'")
        relation_exists = cursor.fetchone() is not None
        
        if not entity_exists:
            # Entity table with embedding column
            cursor.execute("""
                CREATE TABLE entity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    type TEXT,
                    source_doc TEXT,
                    embedding BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            # Check if created_at column exists, add if missing
            cursor.execute("PRAGMA table_info(entity)")
            columns = {row[1] for row in cursor.fetchall()}
            if 'created_at' not in columns:
                cursor.execute("ALTER TABLE entity ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        
        if not relation_exists:
            # Relation table with standard schema
            cursor.execute("""
                CREATE TABLE relation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id INTEGER NOT NULL,
                    target_id INTEGER NOT NULL,
                    relation_type TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    source_doc TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES entity (id),
                    FOREIGN KEY (target_id) REFERENCES entity (id)
                )
            """)
        else:
            # Check if created_at column exists, add if missing
            cursor.execute("PRAGMA table_info(relation)")
            columns = {row[1] for row in cursor.fetchall()}
            if 'created_at' not in columns:
                cursor.execute("ALTER TABLE relation ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_name ON entity (name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relation_source ON relation (source_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relation_target ON relation (target_id)")
        
        self._connection.commit()


class LLMClientSingleton(metaclass=_SingletonMeta):
    """Singleton OpenRouter LLM client."""
    
    def __init__(self):
        self._api_key = None
        
    def get_api_key(self) -> str:
        """Get OpenRouter API key from environment."""
        if self._api_key is None:
            self._api_key = os.getenv("OPENROUTER_API_KEY")
            if not self._api_key:
                raise ValueError("OPENROUTER_API_KEY environment variable not set")
        return self._api_key
    
    async def create_chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = True,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Create a chat completion with streaming."""
        # Ensure API key is available
        self.get_api_key()
        
        # Import here to avoid circular imports and handle missing dependencies
        try:
            from openrouter.client import create_chat_completion
            from openrouter.models.request import ChatCompletionRequest
            
            # Create request with simple dict messages
            request_data = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": stream,
                **kwargs
            }
            
            if max_tokens is not None:
                request_data["max_tokens"] = max_tokens
            
            request = ChatCompletionRequest(**request_data)
            response = await create_chat_completion(request)
            
            if stream:
                # For streaming, use a more defensive approach
                try:
                    # Check if response supports async iteration
                    if hasattr(response, '__aiter__'):
                        # Use type: ignore to suppress type checker warnings for dynamic typing
                        async for chunk in response:  # type: ignore
                            content = self._extract_chunk_content(chunk)
                            if content:
                                yield content
                    else:
                        # Handle as single response
                        content = self._extract_response_content(response)
                        if content:
                            yield content
                except Exception:
                    # Fallback to single response approach
                    content = self._extract_response_content(response)
                    if content:
                        yield content
            else:
                # For non-streaming, extract content directly
                content = self._extract_response_content(response)
                if content:
                    yield content
                        
        except ImportError:
            # Fallback for testing when openrouter is not available
            yield f"Mock LLM response for model {model}: {messages[-1]['content']}"
        except Exception as e:
            # Handle other errors gracefully
            yield f"Error: {str(e)}"
    
    def _extract_chunk_content(self, chunk) -> Optional[str]:
        """Extract content from a streaming chunk."""
        try:
            if hasattr(chunk, 'choices') and chunk.choices:
                choice = chunk.choices[0]
                if hasattr(choice, 'delta') and choice.delta:
                    return getattr(choice.delta, 'content', None)
        except (AttributeError, IndexError, TypeError):
            pass
        return None
    
    def _extract_response_content(self, response) -> Optional[str]:
        """Extract content from a complete response."""
        try:
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message') and choice.message:
                    return getattr(choice.message, 'content', None)
        except (AttributeError, IndexError, TypeError):
            pass
        return None


class NLPSingleton(metaclass=_SingletonMeta):
    """Singleton spaCy NLP pipeline."""
    
    def __init__(self):
        self._nlp = None
        
    def get(self):
        """Get the singleton spaCy pipeline."""
        if self._nlp is None:
            config = get_config()
            logger = LoggerSingleton().get()
            
            logger.info(f"Loading spaCy model: {config.SPACY_MODEL}")
            
            # Load model with only necessary components for performance
            self._nlp = spacy.load(
                config.SPACY_MODEL,
                disable=["parser", "ner", "lemmatizer", "textcat"]
            )
            
        return self._nlp


# Convenience functions for direct access
def get_logger() -> logging.Logger:
    """Get the singleton logger."""
    return LoggerSingleton().get()


def get_embedding_model() -> SentenceTransformer:
    """Get the singleton embedding model."""
    return EmbeddingSingleton().get()


def get_chroma() -> Chroma:
    """Get the singleton Chroma vector store."""
    return ChromaSingleton().get()


def get_sqlite() -> sqlite3.Connection:
    """Get the singleton SQLite connection."""
    return SQLiteSingleton().get()


def get_llm_client() -> LLMClientSingleton:
    """Get the singleton LLM client."""
    return LLMClientSingleton()


def get_nlp():
    """Get the singleton spaCy pipeline."""
    return NLPSingleton().get()


def embed_texts(texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
    """Convenience function to embed texts."""
    return EmbeddingSingleton().embed(texts)
