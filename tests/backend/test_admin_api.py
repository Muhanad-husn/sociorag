"""Test script for the admin API functionality.

This script tests the admin API functionality, specifically the API key update feature.
"""

import asyncio
import sys
import os
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api.admin import ApiKeyUpdate, update_api_keys
from backend.app.core.config import get_config

client = TestClient(app)

class TestAdminAPI(unittest.TestCase):
    """Test cases for admin API functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Save original environment variables to restore later
        self.original_env = os.environ.copy()
        
    def tearDown(self):
        """Clean up after tests."""
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_env)
        
        # Clear config cache
        get_config.cache_clear()
    @patch('backend.app.api.admin.open')
    @patch('pathlib.Path')
    def test_update_api_keys(self, mock_path, mock_open):
        """Test updating API keys via the admin API."""
        # Mock the .env file
        mock_file = MagicMock()
        mock_file.read.return_value = "OPENROUTER_API_KEY=old_key\n"
        mock_file.__enter__.return_value = mock_file
        mock_open.return_value = mock_file
        
        # Mock Path to return a valid path for the .env file
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True
          # Test API key update with new values
        response = client.put(
            "/api/admin/api-keys",
            json={
                "openrouter_api_key": "test_openrouter_key",
                "huggingface_token": "test_huggingface_token"
            }
        )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        
        # Verify that the open function was called to write to the .env file
        mock_open.assert_called()
        
        # Verify that both keys were updated
        updated_keys = response.json()["data"]["updated_keys"]
        self.assertIn("OPENROUTER_API_KEY", updated_keys)
        self.assertIn("HUGGINGFACE_TOKEN", updated_keys)
    
    def test_get_system_config(self):
        """Test retrieving system configuration."""
        response = client.get("/api/admin/config")
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        
        # Check that the response contains the expected configuration keys
        config = response.json()["config_values"]
        self.assertIn("openrouter_api_key_configured", config)
        self.assertIn("huggingface_token_configured", config)
    
    def test_health_check(self):
        """Test the health check endpoint."""
        response = client.get("/api/admin/health")
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertIn("status", response.json())
        self.assertIn("components", response.json())

async def test_admin_api_async():
    """Test admin API functionality asynchronously."""
    print("\n=== Testing Admin API functionality ===")
    
    try:        # Test API key update
        test_api_keys = ApiKeyUpdate(
            openrouter_api_key="test_key_for_openrouter",
            huggingface_token="test_token_for_huggingface"
        )
        
        # Mock the file operations for testing
        with patch('backend.app.api.admin.open'), \
             patch('pathlib.Path') as mock_path:
            
            # Mock Path to return a valid path for the .env file
            mock_path_instance = MagicMock()
            mock_path.return_value = mock_path_instance
            mock_path_instance.exists.return_value = True
            
            # Call the API function directly
            response = await update_api_keys(test_api_keys)
            
            print(f"API key update response: {response}")
            
            if response.success:
                print("\n✅ Admin API key update test completed successfully")
            else:
                print(f"\n❌ Admin API key update test failed: {response.message}")
        
        return response.success
    
    except Exception as e:
        print(f"\n❌ Admin API test failed with exception: {e}")
        return False

if __name__ == "__main__":
    # Run async tests
    asyncio.run(test_admin_api_async())
    
    # Run unittest tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
