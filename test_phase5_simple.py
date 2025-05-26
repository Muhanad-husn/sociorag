#!/usr/bin/env python3
"""Simple test for Phase 5 Q&A API functionality."""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

async def test_phase5_basic():
    """Test basic Phase 5 functionality."""
    print("=== Testing Phase 5: Answer Generation & PDF Export ===\n")
    
    try:
        # Test 1: Import all Phase 5 modules
        print("1. Testing imports...")
        from backend.app.answer.prompt import build_system_prompt, build_user_prompt
        from backend.app.answer.generator import generate_answer_complete
        from backend.app.answer.pdf import save_pdf
        from backend.app.answer.history import append_record
        print("✅ All imports successful")
        
        # Test 2: Test prompt building
        print("\n2. Testing prompt building...")
        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt("What is a knowledge graph?", ["A knowledge graph is a network of entities."])
        print(f"✅ System prompt length: {len(system_prompt)} characters")
        print(f"✅ User prompt length: {len(user_prompt)} characters")
        
        # Test 3: Test PDF creation (without LLM)
        print("\n3. Testing PDF generation...")
        test_answer = """# Test Answer

This is a **test answer** with some formatting:

- Item 1
- Item 2
- Item 3

Here's a paragraph with *italic* text and `code`.

## Citations

[1] Source document example
[2] Another source document
"""
        
        pdf_path = save_pdf(test_answer, "What is a test?", "test_phase5")
        print(f"✅ PDF created at: {pdf_path}")
        print(f"✅ PDF file size: {pdf_path.stat().st_size} bytes")
        
        # Test 4: Test history logging
        print("\n4. Testing history logging...")
        append_record(
            query="What is a test?",
            pdf_path=pdf_path,
            token_count=50,
            context_count=2,
            duration=1.5
        )
        print("✅ History record added")
        
        # Test 5: Test API imports
        print("\n5. Testing API modules...")
        from backend.app.api.qa import router
        from backend.app.main import app
        print("✅ FastAPI modules imported successfully")
        
        print("\n🎉 Phase 5 basic functionality test PASSED!")
        print("\nNext steps:")
        print("- Run the FastAPI server: uvicorn backend.app.main:app --reload")
        print("- Test the /ask endpoint with a real query")
        print("- Check the generated PDF and history logs")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_phase5_basic())
    sys.exit(0 if success else 1)
