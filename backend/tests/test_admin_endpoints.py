"""Unit tests for the admin API endpoints.

This module contains tests for all admin-related endpoints, including:
- System health
- Configuration management
- LLM settings
- API keys
- Maintenance operations
"""

import sys
import os
import json
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

# Add the project root to the Python path
root_path = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, root_path)

# Import the app - using the correct import path
from backend.app.main import create_app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    app = create_app()
    return TestClient(app)


class TestAdminEndpoints:
    """Test cases for the admin API endpoints."""
    
    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/api/admin/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "components" in data
        
    def test_metrics_endpoint(self, client):
        """Test the system metrics endpoint."""
        response = client.get("/api/admin/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "cpu_usage" in data
        assert "memory_usage" in data
        assert "disk_usage" in data
    def test_config_get_endpoint(self, client):
        """Test getting the system configuration."""
        response = client.get("/api/admin/config")
        assert response.status_code == 200
        data = response.json()
        assert "config_values" in data
        
    def test_llm_settings_endpoint(self, client):
        """Test the LLM settings endpoint."""
        # First test GET method (which may not be implemented)
        get_response = client.get("/api/admin/llm-settings")
        
        # If GET is not implemented, this will likely return 405 Method Not Allowed
        if get_response.status_code == 405:
            print("GET method not allowed for LLM settings (this is expected)")
        
        # Test PUT method which should be implemented
        test_settings = {
            "answer_llm_temperature": 0.7
        }
        
        put_response = client.put("/api/admin/llm-settings", json=test_settings)
        
        # Print detailed response for debugging
        print(f"LLM settings PUT response status: {put_response.status_code}")
        print(f"Response content: {put_response.text}")
        
        # Assert proper response
        assert put_response.status_code == 200
        data = put_response.json()
        assert "success" in data
        assert data["success"] is True
        assert "updated_settings" in data["data"]
        assert "answer_llm_temperature" in data["data"]["updated_settings"]
        assert "restart_required" in data["data"]
        assert data["data"]["restart_required"] is True
        
    def test_maintenance_cleanup_endpoint(self, client):
        """Test the system cleanup maintenance endpoint."""
        response = client.post("/api/admin/maintenance/cleanup")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "operation" in data
        assert data["operation"] == "system_cleanup"


if __name__ == "__main__":
    # Run the tests directly
    pytest.main(["-xvs", __file__])
