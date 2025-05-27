"""Tests for Phase 2 Infrastructure Singletons."""

import asyncio
import logging
import sqlite3
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import spacy
from spacy.language import Language
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import Chroma

from app.core.singletons import (
    LoggerSingleton,
    EmbeddingSingleton,
    ChromaSingleton,
    SQLiteSingleton,
    LLMClientSingleton,
    NLPSingleton,
    get_logger,
    get_embedding_model,
    get_chroma,
    get_sqlite,
    get_llm_client,
    get_nlp,
    embed_texts
)


class TestLoggerSingleton:
    """Test LoggerSingleton functionality."""

    def test_singleton_identity(self):
        """Test that the same logger instance is returned."""
        logger1 = LoggerSingleton().get()
        logger2 = LoggerSingleton().get()
        assert logger1 is logger2
        assert isinstance(logger1, logging.Logger)
        assert logger1.name == "sociograph"

    def test_convenience_function(self):
        """Test the convenience function returns the same instance."""
        logger1 = get_logger()
        logger2 = LoggerSingleton().get()
        assert logger1 is logger2


class TestEmbeddingSingleton:
    """Test EmbeddingSingleton functionality."""

    def test_singleton_identity(self):
        """Test that the same embedding model is returned."""
        model1 = EmbeddingSingleton().get()
        model2 = EmbeddingSingleton().get()
        assert model1 is model2
        assert isinstance(model1, SentenceTransformer)

    def test_embed_single_text(self):
        """Test embedding a single text."""
        embedding = EmbeddingSingleton().embed("Hello world")
        assert isinstance(embedding, list)
        assert len(embedding) == 384  # all-MiniLM-L6-v2 dimension    def test_embed_multiple_texts(self):
        """Test embedding multiple texts."""
        embeddings = EmbeddingSingleton().embed(["Hello", "World"])
        assert isinstance(embeddings, list)
        assert len(embeddings) == 2
        # For multiple texts, we should get a list of lists
        assert all(isinstance(emb, list) and len(emb) == 384 for emb in embeddings)

    def test_convenience_function(self):
        """Test the convenience function."""
        embedding1 = embed_texts("test")
        embedding2 = EmbeddingSingleton().embed("test")
        assert embedding1 == embedding2
        # Check that single text returns a list of floats
        assert isinstance(embedding1, list)
        assert all(isinstance(x, float) for x in embedding1)


class TestChromaSingleton:
    """Test ChromaSingleton functionality."""

    def test_singleton_identity(self):
        """Test that the same Chroma instance is returned."""
        chroma1 = ChromaSingleton().get()
        chroma2 = ChromaSingleton().get()
        assert chroma1 is chroma2
        assert isinstance(chroma1, Chroma)

    def test_persistence_directory_created(self):
        """Test that vector directory is created."""
        from app.core.config import get_config
        config = get_config()
        chroma = ChromaSingleton().get()
        assert config.VECTOR_DIR.exists()


class TestSQLiteSingleton:
    """Test SQLiteSingleton functionality."""

    def test_singleton_identity(self):
        """Test that the same connection is returned."""
        conn1 = SQLiteSingleton().get()
        conn2 = SQLiteSingleton().get()
        assert conn1 is conn2
        assert isinstance(conn1, sqlite3.Connection)    
        
    def test_tables_created(self):
        """Test that required tables are created."""
        conn = SQLiteSingleton().get()
        cursor = conn.cursor()
        
        # Check entity table
        cursor.execute("PRAGMA table_info(entity)")
        entity_columns = {row[1] for row in cursor.fetchall()}
        expected_entity_columns = {"id", "name", "embedding"}
        assert expected_entity_columns.issubset(entity_columns)
        
        # Check relation table
        cursor.execute("PRAGMA table_info(relation)")
        relation_columns = {row[1] for row in cursor.fetchall()}
        expected_relation_columns = {"id", "source_id", "target_id", "relation_type", "confidence"}
        assert expected_relation_columns.issubset(relation_columns)

    def test_indexes_created(self):
        """Test that indexes are created."""
        conn = SQLiteSingleton().get()
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA index_list(entity)")
        entity_indexes = {row[1] for row in cursor.fetchall()}
        assert "idx_entity_name" in entity_indexes
        
        cursor.execute("PRAGMA index_list(relation)")
        relation_indexes = {row[1] for row in cursor.fetchall()}
        assert "idx_relation_source" in relation_indexes
        assert "idx_relation_target" in relation_indexes


class TestLLMClientSingleton:
    """Test LLMClientSingleton functionality."""

    def test_singleton_identity(self):
        """Test that the same client instance is returned."""
        client1 = LLMClientSingleton()
        client2 = LLMClientSingleton()
        assert client1 is client2

    @patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test-key'})
    def test_api_key_retrieval(self):
        """Test API key retrieval from environment."""
        client = LLMClientSingleton()
        assert client.get_api_key() == 'test-key'

    def test_missing_api_key_raises_error(self):
        """Test that missing API key raises ValueError."""
        with patch.dict('os.environ', {}, clear=True):            # Clear any cached API key
            client = LLMClientSingleton()
            client._api_key = None
            with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
                client.get_api_key()

    @pytest.mark.asyncio
    @patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test-key'})
    @patch('openrouter.client.create_chat_completion')
    async def test_create_chat_streaming(self, mock_create_chat):
        """Test streaming chat creation."""
        # Mock the async generator
        async def mock_generator():
            mock_chunk = MagicMock()
            mock_chunk.choices = [MagicMock()]
            mock_chunk.choices[0].delta = MagicMock()
            mock_chunk.choices[0].delta.content = "test response"
            yield mock_chunk

        mock_create_chat.return_value = mock_generator()

        client = LLMClientSingleton()
        messages = [{"role": "user", "content": "test"}]
        
        result = []
        async for chunk in client.create_chat("test-model", messages):
            result.append(chunk)
        
        assert result == ["test response"]


class TestNLPSingleton:
    """Test NLPSingleton functionality."""

    def test_singleton_identity(self):
        """Test that the same spaCy pipeline is returned."""
        nlp1 = NLPSingleton().get()
        nlp2 = NLPSingleton().get()
        assert nlp1 is nlp2
        assert isinstance(nlp1, Language)

    def test_nlp_processing(self):
        """Test that the spaCy pipeline works."""
        nlp = NLPSingleton().get()
        doc = nlp("Hello world")
        assert len(doc) == 2
        assert doc[0].text == "Hello"
        assert doc[1].text == "world"

    def test_convenience_function(self):
        """Test the convenience function."""
        nlp1 = get_nlp()
        nlp2 = NLPSingleton().get()
        assert nlp1 is nlp2


class TestThreadSafety:
    """Test thread safety of singletons."""

    def test_logger_thread_safety(self):
        """Test that LoggerSingleton is thread-safe."""
        instances = []
        
        def create_instance():
            instances.append(LoggerSingleton().get())
        
        threads = [threading.Thread(target=create_instance) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # All instances should be the same object
        assert all(instance is instances[0] for instance in instances)

    def test_embedding_thread_safety(self):
        """Test that EmbeddingSingleton is thread-safe."""
        instances = []
        
        def create_instance():
            instances.append(EmbeddingSingleton().get())
        
        threads = [threading.Thread(target=create_instance) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # All instances should be the same object
        assert all(instance is instances[0] for instance in instances)


class TestConvenienceFunctions:
    """Test all convenience functions."""

    def test_all_convenience_functions(self):
        """Test that all convenience functions work and return singletons."""
        logger = get_logger()
        embedding_model = get_embedding_model()
        chroma = get_chroma()
        sqlite_conn = get_sqlite()
        llm_client = get_llm_client()
        nlp = get_nlp()

        # Test they return the correct types
        assert isinstance(logger, logging.Logger)
        assert isinstance(embedding_model, SentenceTransformer)
        assert isinstance(chroma, Chroma)
        assert isinstance(sqlite_conn, sqlite3.Connection)
        assert isinstance(llm_client, LLMClientSingleton)
        assert isinstance(nlp, Language)

        # Test they return the same instances when called again
        assert logger is get_logger()
        assert embedding_model is get_embedding_model()
        assert chroma is get_chroma()
        assert sqlite_conn is get_sqlite()
        assert llm_client is get_llm_client()
        assert nlp is get_nlp()


if __name__ == "__main__":
    # Run a simple test
    print("Testing Phase 2 Singletons...")
    
    # Test logger
    logger = get_logger()
    logger.info("Logger singleton working!")
    
    # Test embedding
    embedding = embed_texts("Hello world")
    print(f"Embedding dimension: {len(embedding)}")
    
    # Test spaCy
    nlp = get_nlp()
    doc = nlp("Hello world")
    print(f"spaCy tokens: {[token.text for token in doc]}")
    
    # Test SQLite
    conn = get_sqlite()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Database tables: {[table[0] for table in tables]}")
    
    print("All Phase 2 singletons working correctly!")
