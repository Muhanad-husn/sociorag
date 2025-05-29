"""Test script for the translation functionality.

This script tests the Arabic translation feature to ensure it's working properly.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.retriever.language import translate_with_llm
from backend.app.core.config import get_config
from backend.app.api.qa import AskRequest, ask_question

async def test_translation_function():
    """Test the direct translation function."""
    print("\n=== Testing direct translation function ===")
    
    english_text = "Hello, this is a test of the translation function."
    print(f"Original text: {english_text}")
    
    try:
        # Test English to Arabic translation
        arabic_text = await translate_with_llm(english_text, "en", "ar")
        print(f"Translated to Arabic: {arabic_text}")
        
        # Test Arabic to English translation
        back_to_english = await translate_with_llm(arabic_text, "ar", "en")
        print(f"Translated back to English: {back_to_english}")
        
        print("\n✅ Translation function test completed")
        return True
    except Exception as e:
        print(f"\n❌ Translation function test failed: {e}")
        return False

async def test_ask_endpoint():
    """Test the ask endpoint with translation."""
    print("\n=== Testing ask endpoint with translation ===")
    
    # Create a test request
    request = AskRequest(
        query="What is a knowledge graph?",
        translate_to_arabic=True,
        temperature=0.7,
        top_k=3,
        top_k_rerank=2
    )
    
    try:
        # Call the ask endpoint
        print("Calling ask endpoint with translation=True...")
        response = await ask_question(request)
        
        print(f"Response language: {response.language}")
        print(f"Answer snippet: {response.answer[:100]}...")
        
        # Check if language is Arabic
        if response.language == "ar":
            print("\n✅ Ask endpoint translation test passed")
            return True
        else:
            print(f"\n❌ Ask endpoint translation test failed: Language is {response.language}, expected 'ar'")
            return False
    except Exception as e:
        print(f"\n❌ Ask endpoint test failed: {e}")
        return False

async def test_configuration():
    """Test the configuration for translation."""
    print("\n=== Testing translation configuration ===")
    
    config = get_config()
    
    print(f"TRANSLATE_LLM_MODEL: {config.TRANSLATE_LLM_MODEL}")
    print(f"HUGGINGFACE_TOKEN configured: {'Yes' if config.HUGGINGFACE_TOKEN else 'No'}")
    
    if not config.HUGGINGFACE_TOKEN:
        print("\n⚠️ Warning: HUGGINGFACE_TOKEN is not configured")
        print("You may need to add it to your .env file:")
        print("HUGGINGFACE_TOKEN=hf_your_token_here")
    
    print("\n✅ Configuration test completed")
    return True

async def main():
    """Run all tests."""
    print("=== Arabic Translation Feature Tests ===")
    
    # Test configuration
    await test_configuration()
    
    # Test direct translation function
    translation_test = await test_translation_function()
    
    # Only test ask endpoint if translation function works
    if translation_test:
        await test_ask_endpoint()
    else:
        print("\n⚠️ Skipping ask endpoint test because translation function failed")
    
    print("\n=== Tests completed ===")

if __name__ == "__main__":
    asyncio.run(main())
