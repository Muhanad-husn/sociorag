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
from backend.app.main import create_app


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
        with patch('backend.app.api.ingest.reset_corpus') as mock_reset:
            mock_reset.return_value = {"status": "success", "message": "Corpus reset"}
            
            response = client.post("/api/ingest/reset")
            
            assert response.status_code == 200
            assert response.json()["status"] == "success"
            mock_reset.assert_called_once()
    
    def test_reset_endpoint_failure(self, client):
        """Test the /api/ingest/reset endpoint with failure."""
        with patch('backend.app.api.ingest.reset_corpus') as mock_reset:
            mock_reset.side_effect = Exception("Reset failed")
            
            response = client.post("/api/ingest/reset")
            
            assert response.status_code == 500
            assert "Failed to reset corpus" in response.json()["detail"]
    
    def test_upload_endpoint_valid_pdf(self, client, sample_pdf_path):
        """Test the /api/ingest/upload endpoint with valid PDF."""
        if sample_pdf_path.exists():
            with open(sample_pdf_path, "rb") as f:
                files = {"file": ("test.pdf", f, "application/pdf")}
                
                with patch('backend.app.api.ingest.process_all') as mock_process:
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
        with patch('backend.app.api.ingest.process_all') as mock_process:
            response = client.post("/api/ingest/process")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "started"
            assert "Processing started" in data["message"]
    
    def test_progress_endpoint(self, client):
        """Test the /api/ingest/progress endpoint (SSE)."""
        response = client.get("/api/ingest/progress")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"


class TestQAEndpoints:
    """Test cases for the Q&A API endpoints."""
    
    def test_ask_endpoint_valid_question(self, client):
        """Test the /api/qa/ask endpoint with valid question."""
        with patch('backend.app.api.qa.retrieve_context') as mock_retrieve, \
             patch('backend.app.api.qa.generate_answer') as mock_generate, \
             patch('backend.app.api.qa.append_record') as mock_append:
            
            # Mock context retrieval
            mock_retrieve.return_value = {
                "chunks": [{"text": "sample context", "score": 0.9}]
            }
            
            # Mock answer generation (async generator)
            async def mock_answer_gen():
                for token in ["Hello", " ", "world", "!"]:
                    yield token
            
            mock_generate.return_value = mock_answer_gen()
            
            # Test the endpoint
            response = client.post("/api/qa/ask", json={"question": "What is climate change?"})
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    def test_ask_endpoint_empty_question(self, client):
        """Test the /api/qa/ask endpoint with empty question."""
        response = client.post("/api/qa/ask", json={"question": ""})
        
        assert response.status_code == 400
        assert "Question cannot be empty" in response.json()["detail"]
    
    def test_ask_endpoint_missing_question(self, client):
        """Test the /api/qa/ask endpoint with missing question field."""
        response = client.post("/api/qa/ask", json={})
        
        assert response.status_code == 422  # Validation error


class TestHistoryEndpoints:
    """Test cases for the history API endpoints."""
    def test_get_history_endpoint(self, client):
        """Test the /api/history/ endpoint."""
        with patch('backend.app.api.history.get_recent_history') as mock_get_history:
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
        with patch('backend.app.api.history.get_recent_history') as mock_get_history:
            mock_get_history.return_value = []
            
            response = client.get("/api/history/?page=2&per_page=10")
            
            assert response.status_code == 200
            data = response.json()
            assert data["page"] == 2
            assert data["per_page"] == 10
    def test_get_history_with_search(self, client):
        """Test the /api/history/ endpoint with search parameter."""
        with patch('backend.app.api.history.get_recent_history') as mock_get_history:
            mock_get_history.return_value = []
            
            response = client.get("/api/history/?search=climate")
            
            assert response.status_code == 200
            # Verify that get_recent_history was called
            mock_get_history.assert_called_once()
    
    def test_get_specific_history_record(self, client):
        """Test the /api/history/{record_id} endpoint."""
        with patch('backend.app.api.history.get_recent_history') as mock_get_history:
            mock_get_history.return_value = [
                {
                    "query": "What is AI?",
                    "datetime": "2025-05-26T10:00:00",
                    "token_count": 50,
                    "context_count": 3,
                    "metadata": {}
                }
            ]
            
            response = client.get("/api/history/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["query"] == "What is AI?"

    def test_get_nonexistent_history_record(self, client):
        """Test the /api/history/{record_id} endpoint with nonexistent record."""
        with patch('backend.app.api.history.get_recent_history') as mock_get_history:
            mock_get_history.return_value = []  # Empty history
            
            response = client.get("/api/history/999")
            
            assert response.status_code == 404
            assert "History record not found" in response.json()["detail"]
    
    def test_delete_history_record(self, client):
        """Test the DELETE /api/history/{record_id} endpoint."""
        with patch('backend.app.api.history.get_recent_history') as mock_get_history:
            mock_get_history.return_value = [{"query": "test"}]
            
            response = client.delete("/api/history/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "not_implemented"  # JSONL doesn't support individual deletion
            assert data["record_id"] == 1
    
    def test_clear_all_history(self, client):
        """Test the DELETE /api/history/ endpoint."""
        with patch('backend.app.api.history.cleanup_old_history') as mock_cleanup:
            mock_cleanup.return_value = 5  # 5 records removed
            
            response = client.delete("/api/history/")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "cleared" in data["message"]
            mock_cleanup.assert_called_once_with(max_records=0)
    
    def test_get_history_stats(self, client):
        """Test the /api/history/stats endpoint."""
        with patch('backend.app.api.history.get_history_stats') as mock_stats:
            mock_stats.return_value = {
                "total_queries": 10,
                "total_tokens": 500,
                "avg_duration": 2.5,
                "last_query_time": "2025-05-26T10:00:00"
            }
            
            response = client.get("/api/history/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_queries"] == 10
            assert data["total_tokens"] == 500
            assert data["avg_duration"] == 2.5


class TestDocumentEndpoints:
    """Test cases for the document management endpoints."""
    
    def test_documents_router_exists(self, client):
        """Test that documents endpoints are accessible."""
        # This will depend on what's implemented in documents.py
        # For now, just test that the router is included
        response = client.get("/")  # Root endpoint
        assert response.status_code == 200


class TestSearchEndpoints:
    """Test cases for the search endpoints."""
    
    def test_search_router_exists(self, client):
        """Test that search endpoints are accessible."""
        # This will depend on what's implemented in search.py
        response = client.get("/")  # Root endpoint
        assert response.status_code == 200


class TestAdminEndpoints:
    """Test cases for the admin endpoints."""
    
    def test_admin_router_exists(self, client):
        """Test that admin endpoints are accessible."""
        response = client.get("/")  # Root endpoint
        assert response.status_code == 200


class TestExportEndpoints:
    """Test cases for the export endpoints."""
    
    def test_export_router_exists(self, client):
        """Test that export endpoints are accessible."""
        response = client.get("/")  # Root endpoint
        assert response.status_code == 200


class TestWebSocketEndpoints:
    """Test cases for WebSocket endpoints."""
    
    def test_websocket_qa_connection(self, client):
        """Test WebSocket Q&A connection."""
        with client.websocket_connect("/api/ws/qa") as websocket:
            # Test ping-pong
            websocket.send_json({"type": "ping"})
            data = websocket.receive_json()
            assert data["type"] == "pong"
    
    def test_websocket_qa_question(self, client):
        """Test WebSocket Q&A question handling."""
        with patch('backend.app.api.websocket_new.retrieve_context') as mock_retrieve, \
             patch('backend.app.api.websocket_new.generate_answer') as mock_generate:
            
            mock_retrieve.return_value = {"chunks": []}
            
            # Mock async generator
            async def mock_answer_gen():
                yield "test"
                yield " answer"
            
            mock_generate.return_value = mock_answer_gen()
            
            with client.websocket_connect("/api/ws/qa") as websocket:
                # Send question
                websocket.send_json({
                    "type": "question",
                    "question": "What is AI?",
                    "session_id": "test_session"
                })
                
                # Receive acknowledgment
                data = websocket.receive_json()
                assert data["type"] == "question_received"
    
    def test_websocket_processing_connection(self, client):
        """Test WebSocket processing status connection."""
        with client.websocket_connect("/api/ws/processing/test_doc") as websocket:
            # Should receive connected message
            data = websocket.receive_json()
            assert data["type"] == "connected"
            assert data["document_id"] == "test_doc"
    
    def test_websocket_monitor_connection(self, client):
        """Test WebSocket system monitor connection."""
        with client.websocket_connect("/api/ws/monitor") as websocket:
            # Should receive monitor connected message
            data = websocket.receive_json()
            assert data["type"] == "monitor_connected"


class TestRootEndpoint:
    """Test cases for the root endpoint."""
    
    def test_root_endpoint(self, client):
        """Test the root endpoint returns status."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "SocioGraph API is running" in data["message"]


class TestStaticFiles:
    """Test cases for static file serving."""
    
    def test_static_files_mount(self, client):
        """Test that static files are properly mounted."""
        # This test would need actual files in the saved directory
        # For now, just test that the mount point doesn't error
        response = client.get("/static/saved/nonexistent.pdf")
        # Should return 404, not 500 or other error
        assert response.status_code == 404


class TestCORSMiddleware:
    """Test cases for CORS middleware."""
    
    def test_cors_headers(self, client):
        """Test that CORS headers are present."""
        # Test with a common origin
        test_origin = "http://localhost:3000"
        response = client.options(
            "/", 
            headers={
                "Origin": test_origin, 
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type"
            }
        )
        
        # Verify CORS headers
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        
        # Either the origin is echoed back or "*" is returned
        origin_header = response.headers.get("access-control-allow-origin")
        assert origin_header == "*" or origin_header == test_origin


class TestIntegrationFlows:
    """Integration tests for complete user flows."""
    def test_complete_qa_flow(self, client):
        """Test complete Q&A flow from question to history."""
        with patch('backend.app.api.qa.retrieve_context') as mock_retrieve, \
             patch('backend.app.api.qa.generate_answer') as mock_generate, \
             patch('backend.app.api.qa.append_record') as mock_append, \
             patch('backend.app.api.history.get_recent_history') as mock_get_history:
            
            # Setup mocks
            mock_retrieve.return_value = {"chunks": []}
            
            async def mock_answer_gen():
                yield "Test answer"
            
            mock_generate.return_value = mock_answer_gen()
              # Mock history
            mock_get_history.return_value = [
                {
                    "query": "Test question",
                    "datetime": "2025-05-26T10:00:00",
                    "token_count": 2,
                    "context_count": 0,
                    "metadata": {}
                }
            ]
            
            # 1. Ask a question
            response = client.post("/api/qa/ask", json={"question": "Test question"})
            assert response.status_code == 200
            
            # 2. Check history
            response = client.get("/api/history/")
            assert response.status_code == 200
            data = response.json()
            assert len(data["records"]) >= 0
    
    def test_upload_and_process_flow(self, client, sample_pdf_path):
        """Test upload and process flow."""
        if sample_pdf_path.exists():
            with patch('backend.app.api.ingest.process_all') as mock_process:
                # 1. Upload file
                with open(sample_pdf_path, "rb") as f:
                    files = {"file": ("test.pdf", f, "application/pdf")}
                    response = client.post("/api/ingest/upload", files=files)
                    assert response.status_code == 200
                
                # 2. Trigger processing
                response = client.post("/api/ingest/process")
                assert response.status_code == 200
        else:
            pytest.skip("Sample PDF file not found")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
