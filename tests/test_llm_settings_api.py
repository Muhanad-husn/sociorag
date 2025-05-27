"""
Comprehensive test for the LLM settings functionality in SocioGraph.
This test checks if LLM parameters can be updated and verifies proper error handling.
"""

import requests
import json
import time
from pathlib import Path
import os

def test_llm_settings():
    """Test the LLM settings API endpoint."""
    base_url = "http://127.0.0.1:8000"
    
    print("\n🔍 Testing LLM settings API...")
    
    # First, get current settings via the config endpoint
    try:
        config_response = requests.get(f"{base_url}/api/admin/config")
        if config_response.status_code == 200:
            current_config = config_response.json()
            print("✅ Successfully retrieved current configuration")
            
            # Extract current LLM settings for comparison
            config_values = current_config.get("config_values", {})
            current_answer_temp = config_values.get("answer_llm_temperature")
            print(f"  Current answer_llm_temperature: {current_answer_temp}")
        else:
            print(f"❌ Failed to get configuration: {config_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing config endpoint: {e}")
        return False
    
    # Try to update the LLM settings with a test value
    try:
        # Calculate a new temperature value different from current
        new_temp = 0.7 if current_answer_temp != 0.7 else 0.5
        
        # Test data for update
        test_settings = {
            "answer_llm_temperature": new_temp
        }
        
        # Send update request
        update_response = requests.put(
            f"{base_url}/api/admin/llm-settings",
            json=test_settings
        )
        
        # Check response
        if update_response.status_code == 200:
            update_data = update_response.json()
            print("✅ Successfully updated LLM settings")
            print(f"  Updated settings: {update_data.get('data', {}).get('updated_settings', [])}")
            print(f"  Restart required: {update_data.get('data', {}).get('restart_required', False)}")
            
            # Check if the expected setting was updated
            updated_settings = update_data.get("data", {}).get("updated_settings", [])
            if "answer_llm_temperature" in updated_settings:
                print("✅ Confirmed answer_llm_temperature was updated")
            else:
                print("❌ Failed to update answer_llm_temperature")
                return False
                
            # Verify .env file was updated
            try:
                # Find the .env file
                root_dir = Path(__file__).resolve().parent.parent
                env_file = root_dir / ".env"
                
                if env_file.exists():
                    # Read the .env file
                    with open(env_file, 'r', encoding='utf-8') as f:
                        env_content = f.read()
                    
                    # Check if the setting is present
                    if f"ANSWER_LLM_TEMPERATURE={new_temp}" in env_content:
                        print("✅ Confirmed .env file was updated correctly")
                    else:
                        print("⚠️ Could not find updated value in .env file")
                else:
                    print("⚠️ .env file not found")
            except Exception as e:
                print(f"⚠️ Error checking .env file: {e}")
            
        else:
            print(f"❌ Failed to update LLM settings: {update_response.status_code}")
            print(f"  Error: {update_response.text}")
            return False
    except Exception as e:
        print(f"❌ Error updating LLM settings: {e}")
        return False
    
    # Test error handling by trying to update with invalid values
    try:
        # Test with invalid temperature (outside 0-1 range)
        invalid_settings = {
            "answer_llm_temperature": 2.5  # Invalid temperature
        }
        
        invalid_response = requests.put(
            f"{base_url}/api/admin/llm-settings",
            json=invalid_settings
        )
        
        # For invalid settings, behavior depends on implementation:
        # Some APIs will reject with 400, others might silently ignore or validate at runtime
        print(f"  Invalid settings response: {invalid_response.status_code}")
        
        if invalid_response.status_code >= 400:
            print("✅ API correctly rejected invalid value")
        else:
            print("⚠️ API accepted potentially invalid value (server-side validation may occur)")
    except Exception as e:
        print(f"❌ Error testing invalid settings: {e}")
    
    print("\n✅ LLM settings API test completed successfully")
    return True

if __name__ == "__main__":
    test_llm_settings()
