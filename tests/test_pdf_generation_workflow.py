#!/usr/bin/env python3
"""
PDF Generation User Choice - Complete Workflow Test

This test suite verifies the PDF generation user choice functionality
implemented for SocioRAG. It tests:

1. Backend API endpoints with generate_pdf parameter
2. PDF generation enabled/disabled scenarios  
3. Arabic language support with PDF options
4. Both GET and POST API endpoints
5. Complete workflow functionality

Usage:
    python tests/test_pdf_generation_workflow.py

Environment Variables:
    SOCIORAG_API_URL: Backend API URL (default: http://127.0.0.1:8000)
    SOCIORAG_FRONTEND_URL: Frontend URL (default: http://localhost:5173)

Requirements:
    - Backend server running
    - requests library installed
"""

import requests
import json
import time
import os
import pytest

# Use environment variable or default to standard development ports
BASE_URL = os.environ.get("SOCIORAG_API_URL", "http://127.0.0.1:8000")
FRONTEND_URL = os.environ.get("SOCIORAG_FRONTEND_URL", "http://localhost:5173")

@pytest.mark.integration
def test_backend_functionality():
    """Test backend PDF generation functionality."""
    print("🔧 Testing Backend Functionality...")
    
    # Test health endpoint
    try:
        health = requests.get(f"{BASE_URL}/api/admin/health")
        if health.status_code == 200:
            print("✅ Backend health check passed")
        else:
            print(f"❌ Backend health check failed: {health.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False
    
    # Test PDF enabled
    print("\n📄 Testing PDF Generation ENABLED...")
    response = requests.post(f"{BASE_URL}/api/qa/ask", json={
        "query": "What is machine learning?",
        "generate_pdf": True
    })
    
    if response.status_code == 200:
        data = response.json()
        pdf_url = data.get('pdf_url', '')
        if pdf_url:
            print(f"✅ PDF generated: {pdf_url}")
        else:
            print("❌ PDF not generated when enabled")
            return False
    else:
        print(f"❌ API request failed: {response.status_code}")
        return False
    
    # Test PDF disabled
    print("\n🚫 Testing PDF Generation DISABLED...")
    response = requests.post(f"{BASE_URL}/api/qa/ask", json={
        "query": "What is deep learning?",
        "generate_pdf": False
    })
    
    if response.status_code == 200:
        data = response.json()
        pdf_url = data.get('pdf_url', '')
        if not pdf_url:
            print("✅ PDF not generated when disabled")
        else:
            print(f"❌ PDF generated when disabled: {pdf_url}")
            return False
    else:
        print(f"❌ API request failed: {response.status_code}")
        return False
      return True

@pytest.mark.integration
def test_arabic_functionality():
    """Test Arabic language functionality with PDF."""
    print("\n🌍 Testing Arabic Language Support...")
    
    # Test Arabic with PDF enabled
    response = requests.post(f"{BASE_URL}/api/qa/ask", json={
        "query": "ما هو الذكاء الاصطناعي؟",
        "translate_to_arabic": True,
        "generate_pdf": True
    })
    
    if response.status_code == 200:
        data = response.json()
        answer = data.get('answer', '')
        pdf_url = data.get('pdf_url', '')
        language = data.get('language', '')
        
        print(f"✅ Arabic response received (length: {len(answer)})")
        print(f"   Language: {language}")
        print(f"   PDF URL: {pdf_url if pdf_url else 'None'}")
        
        if pdf_url:
            print("✅ Arabic PDF generated successfully")
        else:
            print("❌ Arabic PDF not generated")
            return False
    else:
        print(f"❌ Arabic API request failed: {response.status_code}")
        return False
    
    # Test Arabic with PDF disabled
    response = requests.post(f"{BASE_URL}/api/qa/ask", json={
        "query": "ما هو التعلم العميق؟",
        "translate_to_arabic": True,
        "generate_pdf": False
    })
    
    if response.status_code == 200:
        data = response.json()
        pdf_url = data.get('pdf_url', '')
        if not pdf_url:
            print("✅ Arabic response without PDF as expected")
        else:
            print(f"❌ Arabic PDF generated when disabled: {pdf_url}")
            return False
    else:
        print(f"❌ Arabic API request failed: {response.status_code}")
        return False
      return True

@pytest.mark.integration  
def test_api_endpoints():
    """Test both GET and POST endpoints."""
    print("\n🔄 Testing API Endpoints...")
    
    # Test POST endpoint
    post_response = requests.post(f"{BASE_URL}/api/qa/ask", json={
        "query": "What is neural network?",
        "generate_pdf": True
    })
    
    if post_response.status_code == 200:
        print("✅ POST endpoint working")
    else:
        print(f"❌ POST endpoint failed: {post_response.status_code}")
        return False
    
    # Test GET endpoint
    get_response = requests.get(f"{BASE_URL}/api/qa/ask", params={
        "query": "What is computer vision?",
        "generate_pdf": False
    })
    
    if get_response.status_code == 200:
        data = get_response.json()
        pdf_url = data.get('pdf_url', '')
        if not pdf_url:
            print("✅ GET endpoint working (PDF disabled)")
        else:
            print(f"❌ GET endpoint: PDF generated when disabled: {pdf_url}")
            return False
    else:
        print(f"❌ GET endpoint failed: {get_response.status_code}")
        return False
    
    return True

def print_workflow_instructions():
    """Print manual testing instructions for the UI."""
    print("\n" + "="*60)
    print("🎯 MANUAL UI TESTING INSTRUCTIONS")
    print("="*60)
    print(f"1. Open your browser to: {FRONTEND_URL}")
    print("2. Go to Settings page")
    print("3. Verify PDF Generation toggle is visible")
    print("4. Test with PDF Generation ENABLED:")
    print("   - Enable the PDF Generation toggle")
    print("   - Ask a question")
    print("   - Verify PDF download button appears")
    print("   - Click download and verify PDF is downloaded")
    print("5. Test with PDF Generation DISABLED:")
    print("   - Disable the PDF Generation toggle")
    print("   - Ask a question")
    print("   - Verify NO PDF download button appears")
    print("6. Test Arabic functionality:")
    print("   - Enable Arabic translation")
    print("   - Test both PDF enabled/disabled scenarios")
    print("   - Verify RTL display works correctly")
    print("="*60)

def main():
    """Run complete test suite."""
    print("🚀 SocioRAG PDF Generation - Complete Workflow Test")
    print("="*60)
    
    # Backend functionality tests
    if not test_backend_functionality():
        print("❌ Backend tests failed")
        return False
    
    # Arabic functionality tests
    if not test_arabic_functionality():
        print("❌ Arabic tests failed")
        return False
    
    # API endpoints tests
    if not test_api_endpoints():
        print("❌ API endpoint tests failed")
        return False
    
    print("\n✅ All automated tests passed!")
    
    # Manual UI testing instructions
    print_workflow_instructions()
    
    print("\n🎉 PDF Generation User Choice Implementation Complete!")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
