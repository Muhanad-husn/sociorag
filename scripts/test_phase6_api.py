#!/usr/bin/env python
"""
SocioGraph API Endpoints Tester

This script provides simple functions for testing the SocioGraph API endpoints
after Phase 6 implementation.

Usage:
    python test_phase6_api.py [endpoint]

Available endpoints:
    reset            - Test corpus reset
    upload           - Test PDF upload
    process          - Test manual processing
    progress         - Test progress streaming
    ask              - Test Q&A with streaming
    history          - Test history retrieval
    websocket        - Test WebSocket connection
    all              - Test all endpoints
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
import requests
import websockets

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"
WS_BASE = f"ws://localhost:8000/api/ws"

# Sample PDF path - adjust as needed
SAMPLE_PDF = Path("D:/sociorag/input/climate_article.pdf")

# Sample question
SAMPLE_QUESTION = "What are the main themes in the document?"


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")


def print_response(response, show_headers=False):
    """Print a formatted HTTP response."""
    print(f"Status: {response.status_code}")
    
    if show_headers:
        print("\nHeaders:")
        for k, v in response.headers.items():
            print(f"  {k}: {v}")
    
    try:
        print("\nResponse:")
        print(json.dumps(response.json(), indent=2))
    except:
        print("\nResponse (raw):")
        print(response.text[:500] + ("..." if len(response.text) > 500 else ""))


def test_reset():
    """Test the /api/ingest/reset endpoint."""
    print_header("Testing /api/ingest/reset")
    
    response = requests.post(f"{API_BASE}/ingest/reset")
    print_response(response)


def test_upload():
    """Test the /api/ingest/upload endpoint."""
    print_header("Testing /api/ingest/upload")
    
    if not SAMPLE_PDF.exists():
        print(f"Error: Sample PDF not found at {SAMPLE_PDF}")
        print("Please adjust the SAMPLE_PDF path in the script.")
        return
    
    with open(SAMPLE_PDF, "rb") as f:
        files = {"file": (SAMPLE_PDF.name, f, "application/pdf")}
        response = requests.post(f"{API_BASE}/ingest/upload", files=files)
        print_response(response)


def test_process():
    """Test the /api/ingest/process endpoint."""
    print_header("Testing /api/ingest/process")
    
    response = requests.post(f"{API_BASE}/ingest/process")
    print_response(response)


def test_progress():
    """Test the /api/ingest/progress endpoint (SSE)."""
    print_header("Testing /api/ingest/progress (SSE)")
    
    print("Connecting to SSE stream (will timeout after 10 seconds)...")
    
    try:
        with requests.get(f"{API_BASE}/ingest/progress", stream=True, timeout=10) as response:
            print(f"Status: {response.status_code}")
            print("\nHeaders:")
            for k, v in response.headers.items():
                print(f"  {k}: {v}")
            
            print("\nEvents:")
            start_time = time.time()
            for line in response.iter_lines():
                if line:
                    print(line.decode('utf-8'))
                
                # Break after 10 seconds to prevent hanging
                if time.time() - start_time > 10:
                    print("\nTimeout reached (10 seconds). Stopping.")
                    break
    except requests.exceptions.Timeout:
        print("\nSSE stream timed out after 10 seconds.")
    except Exception as e:
        print(f"\nError: {str(e)}")


def test_ask():
    """Test the /api/qa/ask endpoint (SSE)."""
    print_header("Testing /api/qa/ask (SSE)")
    
    data = {"question": SAMPLE_QUESTION}
    headers = {"Content-Type": "application/json"}
    
    print(f"Question: {SAMPLE_QUESTION}")
    print("Connecting to SSE stream (will timeout after 30 seconds)...")
    
    try:
        with requests.post(f"{API_BASE}/qa/ask", json=data, headers=headers, stream=True, timeout=30) as response:
            print(f"Status: {response.status_code}")
            
            print("\nEvents:")
            tokens = []
            start_time = time.time()
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    print(line_text)
                    
                    # Extract token if it's a token event
                    if line_text.startswith("event: token") and len(line_text) > 12:
                        try:
                            next_line = next(response.iter_lines()).decode('utf-8')
                            if next_line.startswith("data: "):
                                token = next_line[6:]
                                tokens.append(token)
                        except:
                            pass
                
                # Break after 30 seconds to prevent hanging
                if time.time() - start_time > 30:
                    print("\nTimeout reached (30 seconds). Stopping.")
                    break
            
            if tokens:
                print("\nCollected tokens:")
                print("".join(tokens))
    except requests.exceptions.Timeout:
        print("\nSSE stream timed out after 30 seconds.")
    except Exception as e:
        print(f"\nError: {str(e)}")


def test_history():
    """Test the /api/history/ endpoint."""
    print_header("Testing /api/history/")
    
    response = requests.get(f"{API_BASE}/history/")
    print_response(response)
    
    print("\n" + "-" * 40 + "\n")
    print("Testing /api/history/stats")
    
    response = requests.get(f"{API_BASE}/history/stats")
    print_response(response)


async def test_websocket_async():
    """Test the WebSocket endpoints asynchronously."""
    print_header("Testing WebSocket Endpoints")
    
    print("Connecting to /api/ws/qa...")
    
    try:
        async with websockets.connect(f"{WS_BASE}/qa") as websocket:
            print("Connected! Sending ping...")
            
            # Send ping
            await websocket.send(json.dumps({"type": "ping"}))
            
            # Wait for pong
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print(f"Received: {response}")
            
            # Send question
            print("\nSending question...")
            await websocket.send(json.dumps({
                "type": "question",
                "question": SAMPLE_QUESTION,
                "session_id": "test_session"
            }))
            
            # Wait for responses with timeout
            print("\nReceiving responses (timeout after 10 messages or 30 seconds)...")
            start_time = time.time()
            for i in range(10):  # Limit to 10 messages
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"Received [{i+1}]: {response}")
                    
                    # Check if it's the completion message
                    try:
                        data = json.loads(response)
                        if data.get("type") == "answer_complete":
                            print("\nAnswer complete, exiting.")
                            break
                    except:
                        pass
                    
                except asyncio.TimeoutError:
                    print("Response timeout reached.")
                    break
                
                # Overall timeout
                if time.time() - start_time > 30:
                    print("\nTimeout reached (30 seconds). Stopping.")
                    break
            
    except Exception as e:
        print(f"WebSocket Error: {str(e)}")


def test_websocket():
    """Test the WebSocket endpoints."""
    asyncio.run(test_websocket_async())


def test_all():
    """Run all tests."""
    test_reset()
    test_upload()
    test_process()
    test_progress()
    test_ask()
    test_history()
    test_websocket()


def main():
    """Main entry point."""
    print_header("SocioGraph API Endpoints Tester")
    
    # Check if server is running
    try:
        response = requests.get(BASE_URL)
        if response.status_code != 200:
            print(f"Error: Server returned status code {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to server at {BASE_URL}")
        print("Make sure the server is running with: python -m backend.app.main")
        return
    
    print(f"Server is running at {BASE_URL}")
    print(f"API documentation available at {BASE_URL}/docs")
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("\nPlease specify which endpoint to test:")
        print("  python test_phase6_api.py reset     # Test corpus reset")
        print("  python test_phase6_api.py upload    # Test PDF upload")
        print("  python test_phase6_api.py process   # Test manual processing")
        print("  python test_phase6_api.py progress  # Test progress streaming")
        print("  python test_phase6_api.py ask       # Test Q&A with streaming")
        print("  python test_phase6_api.py history   # Test history retrieval")
        print("  python test_phase6_api.py websocket # Test WebSocket connection")
        print("  python test_phase6_api.py all       # Test all endpoints")
        return
    
    # Run the specified test
    command = sys.argv[1].lower()
    
    if command == "reset":
        test_reset()
    elif command == "upload":
        test_upload()
    elif command == "process":
        test_process()
    elif command == "progress":
        test_progress()
    elif command == "ask":
        test_ask()
    elif command == "history":
        test_history()
    elif command == "websocket":
        test_websocket()
    elif command == "all":
        test_all()
    else:
        print(f"Unknown command: {command}")
        print("Please use one of: reset, upload, process, progress, ask, history, websocket, all")


if __name__ == "__main__":
    main()
