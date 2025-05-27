"""Comprehensive API tests for SocioGraph Phase 6.

This module tests all API endpoints to ensure they work correctly
and meet the Phase 6 requirements.
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import WebSocket

# Import the FastAPI app
from app.main import create_app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_pdf_path():
    """Path to a sample PDF file for testing."""
    return Path("d:/sociorag/input/climate_article.pdf")


class TestIngestEndpoints:
    """Test cases for the ingest API endpoints."""
    def test_reset_endpoint(self, client):
        """Test the /api/ingest/reset endpoint."""
        with patch('app.api.ingest.reset_corpus') as mock_reset:
            mock_reset.return_value = {"status": "corpus cleared"}
            
            response = client.post("/api/ingest/reset")
            
            assert response.status_code == 200
            assert response.json()["status"] == "corpus cleared"
            mock_reset.assert_called_once()

    def test_reset_endpoint_failure(self, client):
        """Test the /api/ingest/reset endpoint with failure."""
        with patch('app.api.ingest.reset_corpus') as mock_reset:
            mock_reset.side_effect = Exception("Reset failed")
            
            response = client.post("/api/ingest/reset")
            
            assert response.status_code == 500
            assert "Failed to reset corpus" in response.json()["detail"]
    
    def test_upload_endpoint_valid_pdf(self, client, sample_pdf_path):
        """Test the /api/ingest/upload endpoint with valid PDF."""
        if sample_pdf_path.exists():
            with open(sample_pdf_path, "rb") as f:
                files = {"file": ("test.pdf", f, "application/pdf")}
                
                with patch('app.api.ingest.process_all') as mock_process:
                    response = client.post("/api/ingest/upload", files=files)
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["status"] == "uploaded"
                    assert "test.pdf" in data["file"]
        else:
            pytest.skip("Sample PDF file not found")
    
    def test_upload_endpoint_invalid_file(self, client):
        """Test the /api/ingest/upload endpoint with invalid file type."""
        files = {"file": ("test.txt", b"test content", "text/plain")}
        
        response = client.post("/api/ingest/upload", files=files)
        
        assert response.status_code == 400
        assert "Only PDF files are supported" in response.json()["detail"]
    
    def test_process_endpoint(self, client):
        """Test the /api/ingest/process endpoint."""
        with patch('app.api.ingest.process_all') as mock_process:
            response = client.post("/api/ingest/process")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "started"
            assert "Processing started" in data["message"]
    
    def test_progress_endpoint(self, client):
        """Test the /api/ingest/progress endpoint (SSE)."""
        response = client.get("/api/ingest/progress")
        
        # SSE endpoints should return 200 with text/event-stream content type
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]


class TestQAEndpoints:
    """Test cases for the Q&A API endpoints."""
    
    @patch('app.retriever.retrieve_context')
    @patch('app.answer.generator.generate_answer')
    def test_ask_endpoint_streaming(self, mock_generate, mock_retrieve, client):
        """Test the /api/qa/ask endpoint with streaming."""
        # Mock retrieval
        mock_retrieve.return_value = {
            "context": ["sample context text"],
            "chunks": [{"text": "sample context", "score": 0.9}]
        }
        
        # Mock answer generation (async generator)
        async def mock_answer_gen():
            for token in ["Hello", " ", "world", "!"]:
                yield token
        
        mock_generate.return_value = mock_answer_gen()
        
        # Test the endpoint
        response = client.post("/api/qa/ask", json={"query": "What is climate change?"})
        
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
    
    def test_ask_endpoint_empty_question(self, client):
        """Test the /api/qa/ask endpoint with empty question."""
        response = client.post("/api/qa/ask", json={"query": ""})
        
        assert response.status_code == 400
        assert "Query cannot be empty" in response.json()["detail"]
    
    def test_ask_endpoint_missing_question(self, client):
        """Test the /api/qa/ask endpoint with missing query field."""
        response = client.post("/api/qa/ask", json={})
        
        assert response.status_code == 422  # Validation error


class TestHistoryEndpoints:
    """Test cases for the history API endpoints."""
    def test_get_history_endpoint(self, client):
        """Test the /api/history/ endpoint."""
        with patch('app.api.history_new.get_recent_history') as mock_get_history:
            mock_get_history.return_value = [
                {
                    "query": "What is AI?",
                    "datetime": "2025-05-26T10:00:00",
                    "token_count": 50,
                    "context_count": 3,
                    "metadata": {}
                }
            ]
            
            response = client.get("/api/history/")
            
            assert response.status_code == 200
            data = response.json()
            assert "records" in data
            assert "total" in data
            assert "page" in data
            assert len(data["records"]) >= 0
    def test_get_history_with_pagination(self, client):
        """Test the /api/history/ endpoint with pagination parameters."""
        with patch('app.api.history_new.get_recent_history') as mock_get_history:
            mock_get_history.return_value = []
            
            response = client.get("/api/history/?page=2&per_page=10")
            
            assert response.status_code == 200
            data = response.json()
            assert "records" in data
            assert data["page"] == 2
            assert data["per_page"] == 10
    def test_get_history_stats_endpoint(self, client):
        """Test the /api/history/stats endpoint."""
        with patch('app.api.history_new.get_history_stats') as mock_stats:
            mock_stats.return_value = {
                "total_queries": 100,
                "avg_tokens": 50.5,
                "avg_context_count": 3.2
            }
            
            response = client.get("/api/history/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert "total_queries" in data


class TestRootEndpoint:
    """Test cases for the root endpoint."""
    
    def test_root_endpoint(self, client):
        """Test the root / endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
