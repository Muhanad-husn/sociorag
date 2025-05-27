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

# Import the embedding cache if available, with fallback
try:
    from backend.app.retriever.embedding_cache import get_embedding_cache
    _EMBEDDING_CACHE_AVAILABLE = True
except ImportError:
    _EMBEDDING_CACHE_AVAILABLE = False


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
    """Singleton logger instance with file and console logging."""
    
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
            
            # Add handlers if none exist
            if not self._logger.handlers:
                # Create logs directory
                logs_dir = config.BASE_DIR / "logs"
                logs_dir.mkdir(exist_ok=True)
                
                # Create formatter
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                
                # Console handler
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(formatter)
                self._logger.addHandler(console_handler)
                
                # File handler with rotation
                from logging.handlers import RotatingFileHandler
                file_handler = RotatingFileHandler(
                    logs_dir / "sociorag.log",
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=5
                )
                file_handler.setFormatter(formatter)
                self._logger.addHandler(file_handler)
                
                # Debug file handler for detailed logs
                debug_handler = RotatingFileHandler(
                    logs_dir / "sociorag_debug.log",
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=3
                )
                debug_handler.setLevel(logging.DEBUG)
                debug_handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
                ))
                self._logger.addHandler(debug_handler)
                
                # Error file handler for errors only
                error_handler = RotatingFileHandler(
                    logs_dir / "sociorag_errors.log",
                    maxBytes=5*1024*1024,   # 5MB
                    backupCount=3
                )
                error_handler.setLevel(logging.ERROR)
                error_handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s\n%(exc_info)s'
                ))
                self._logger.addHandler(error_handler)
                
        return self._logger


class EmbeddingSingleton(metaclass=_SingletonMeta):
    """Singleton sentence transformer model."""
    
    def __init__(self):
        self._model = None
        self._logger = None
        
    def get(self) -> SentenceTransformer:
        """Get the singleton embedding model."""
        if self._model is None:
            config = get_config()
            logger = LoggerSingleton().get()
            self._logger = logger  # Store logger for later use
            logger.info(f"Loading embedding model: {config.EMBEDDING_MODEL}")
            try:
                # Use trust_remote_code=True to avoid authentication issues
                self._model = SentenceTransformer(config.EMBEDDING_MODEL, trust_remote_code=True)
            except Exception as e:
                logger.warning(f"Error loading embedding model with trust_remote_code=True: {e}")
                # Fallback to basic loading
                self._model = SentenceTransformer(config.EMBEDDING_MODEL)
            
        return self._model
        
    def embed(self, texts: Union[str, List[str]], 
              use_cache: bool = True) -> Union[List[float], List[List[float]]]:
        """Embed text(s) and return embeddings.
        
        Args:
            texts: Text or list of texts to embed
            use_cache: Whether to use the embedding cache (default: True)
            
        Returns:
            List of embeddings (list of floats for single text, list of list of floats for multiple texts)
        """
        logger = self._logger or LoggerSingleton().get()
        
        # Check cache first if enabled and available
        if use_cache and _EMBEDDING_CACHE_AVAILABLE:
            try:
                cache = get_embedding_cache()
                cached_embedding = cache.get(texts)
                if cached_embedding is not None:
                    logger.debug(f"Using cached embedding for text(s)")
                    return cached_embedding
            except Exception as e:
                # If there's any error with the cache, log it and continue with normal embedding
                logger.warning(f"Error using embedding cache: {e}")
        
        # If not in cache or cache not enabled, embed normally
        model = self.get()
        
        # Process differently based on text length and count
        is_batch = isinstance(texts, list)
        batch_size = 0
        
        if is_batch:
            batch_size = len(texts)
            logger.debug(f"Embedding batch of {batch_size} texts")
            
            # For very large batches, process in chunks to avoid memory issues
            if batch_size > 100:
                chunk_size = 50
                result = []
                
                for i in range(0, batch_size, chunk_size):
                    end_idx = min(i + chunk_size, batch_size)
                    logger.debug(f"Processing batch chunk {i} to {end_idx}")
                    chunk = texts[i:end_idx]
                    chunk_embeddings = model.encode(chunk)
                    result.extend([emb.tolist() for emb in chunk_embeddings])
                    
                # Store in cache
                if use_cache and _EMBEDDING_CACHE_AVAILABLE:
                    try:
                        cache = get_embedding_cache()
                        for i, text in enumerate(texts):
                            cache.set(text, result[i])
                    except Exception as e:
                        logger.warning(f"Error storing batch in embedding cache: {e}")
                
                return result
        
        # Standard processing for single text or small batches
        embeddings = model.encode(texts)
        
        result = None
        if is_batch:
            result = [emb.tolist() for emb in embeddings]
        else:
            result = embeddings.tolist()
            
        # Store in cache if available
        if use_cache and _EMBEDDING_CACHE_AVAILABLE:
            try:
                cache = get_embedding_cache()
                cache.set(texts, result)
            except Exception as e:
                # If there's any error with the cache, log it but don't fail
                logger.warning(f"Error storing in embedding cache: {e}")
                    
        return result


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
            
            # Set row_factory to return rows as dictionaries
            self._connection.row_factory = sqlite3.Row
            
            # Enable WAL mode for better concurrency
            self._connection.execute("PRAGMA journal_mode=WAL")# Try to load sqlite-vec extension
            try:
                import sqlite_vec
                # Use the load method from sqlite_vec
                sqlite_vec.load(self._connection)
                logger.info("Loaded sqlite-vec extension using sqlite_vec.load()")
            except Exception as e:
                try:
                    # Fallback to manual loading
                    self._connection.enable_load_extension(True)
                    extension_path = sqlite_vec.loadable_path()
                    logger.info(f"SQLite-vec extension path: {extension_path}")
                    self._connection.load_extension(extension_path)
                    logger.info("Loaded sqlite-vec extension from path")
                except Exception as inner_e:
                    logger.warning(f"Could not load sqlite-vec extension: {inner_e}")
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
        """Get OpenRouter API key from configuration."""
        if self._api_key is None:
            from .config import get_config
            cfg = get_config()
            self._api_key = cfg.OPENROUTER_API_KEY
            if not self._api_key:
                raise ValueError("OPENROUTER_API_KEY not set in configuration or environment variables")
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
            
            # For non-streaming, use a simpler approach
            if not stream:
                response = await create_chat_completion(request)
                content = self._extract_response_content(response)
                if content:
                    yield content
                else:
                    # Log raw response for debugging
                    import logging
                    logging.debug(f"Raw non-streaming response: {response}")
                    yield f"Error: Could not extract content from response"
                return
            
            # For streaming, handle chunks
            response = await create_chat_completion(request)
            
            # Use type: ignore to suppress type checker warnings for dynamic typing
            complete_content = ""
            async for chunk in response:  # type: ignore
                content = self._extract_chunk_content(chunk)
                if content:
                    complete_content += content
                    yield content
            
            # If streaming resulted in empty content, try to extract from the full response
            if not complete_content:
                # Log raw response for debugging
                import logging
                logging.debug(f"Raw streaming response produced no content.")
                yield f"Error: No content from streaming response"
                        
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

    async def create_entity_extraction_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: Optional[bool] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Create a chat completion for entity extraction with task-specific defaults."""
        from .config import get_config
        config = get_config()
        
        # Use task-specific defaults from config, but allow overrides
        model = model or config.ENTITY_LLM_MODEL
        temperature = temperature if temperature is not None else config.ENTITY_LLM_TEMPERATURE
        max_tokens = max_tokens if max_tokens is not None else config.ENTITY_LLM_MAX_TOKENS
        stream = stream if stream is not None else config.ENTITY_LLM_STREAM
        
        async for token in self.create_chat(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            **kwargs
        ):
            yield token
            
    async def create_answer_generation_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: Optional[bool] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Create a chat completion for answer generation with task-specific defaults."""
        from .config import get_config
        config = get_config()
        
        # Use task-specific defaults from config, but allow overrides
        model = model or config.ANSWER_LLM_MODEL
        temperature = temperature if temperature is not None else config.ANSWER_LLM_TEMPERATURE
        max_tokens = max_tokens if max_tokens is not None else config.ANSWER_LLM_MAX_TOKENS
        stream = stream if stream is not None else config.ANSWER_LLM_STREAM
        
        # Add context window if specified in config
        if hasattr(config, 'ANSWER_LLM_CONTEXT_WINDOW') and 'context_window' not in kwargs:
            kwargs['context_window'] = config.ANSWER_LLM_CONTEXT_WINDOW
        
        async for token in self.create_chat(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            **kwargs
        ):
            yield token
            
    async def create_translation_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: Optional[bool] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Create a chat completion for translation with task-specific defaults."""
        from .config import get_config
        config = get_config()
        
        # Use task-specific defaults from config, but allow overrides
        model = model or config.TRANSLATE_LLM_MODEL
        temperature = temperature if temperature is not None else config.TRANSLATE_LLM_TEMPERATURE
        max_tokens = max_tokens if max_tokens is not None else config.TRANSLATE_LLM_MAX_TOKENS
        stream = stream if stream is not None else config.TRANSLATE_LLM_STREAM
        
        async for token in self.create_chat(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            **kwargs
        ):
            yield token


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


def embed_texts(texts: Union[str, List[str]], use_cache: bool = True) -> Union[List[float], List[List[float]]]:
    """Convenience function to embed texts.
    
    Args:
        texts: Text or list of texts to embed
        use_cache: Whether to use the embedding cache (default: True)
        
    Returns:
        List of embeddings (list of floats for single text, list of list of floats for multiple texts)
    """
    return EmbeddingSingleton().embed(texts, use_cache=use_cache)

def extract_vector(embedding: Union[List[float], List[List[float]]]) -> List[float]:
    """Extract a vector from potentially nested embeddings.
    
    Args:
        embedding: An embedding vector or list of embedding vectors
        
    Returns:
        A flat list of floats representing the embedding vector
    """
    # Handle case where embedding is a list of lists (batch embeddings)
    if isinstance(embedding, list) and embedding and isinstance(embedding[0], list):
        return embedding[0]  # Take first embedding from batch
    return embedding  # Already a flat list

def calculate_cosine_similarity(vec1: Union[List[float], List[List[float]]], vec2: Union[List[float], List[List[float]]]) -> float:
    """Calculate cosine similarity between two vectors.
    
    Provides a centralized implementation for consistent similarity calculations.
    
    Args:
        vec1: First vector as a list of float values or list of list of float values
        vec2: Second vector as a list of float values or list of list of float values
        
    Returns:
        Cosine similarity score between 0 and 1
    """
    # Ensure we're working with flat lists of floats
    # If vec1 is a list of lists (batch embeddings) and not empty, take first element
    if isinstance(vec1, list) and vec1 and isinstance(vec1[0], list):
        v1 = vec1[0]
    else:
        v1 = vec1
        
    # Same for vec2
    if isinstance(vec2, list) and vec2 and isinstance(vec2[0], list):
        v2 = vec2[0]
    else:
        v2 = vec2
        
    # Calculate dot product
    dot_product = sum(float(a) * float(b) for a, b in zip(v1, v2))
    
    # Calculate magnitudes
    magnitude1 = (sum(float(a) * float(a) for a in v1)) ** 0.5 # type: ignore
    magnitude2 = (sum(float(b) * float(b) for b in v2)) ** 0.5
    
    # Calculate cosine similarity
    if magnitude1 > 0 and magnitude2 > 0:
        return float(dot_product / (magnitude1 * magnitude2))
    else:
        return 0.0
