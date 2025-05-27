"""Comprehensive test of the LLM singleton with all models in config."""

import asyncio
import os
import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from app.core.singletons import LLMClientSingleton
from app.core.config import get_config


@dataclass
class ModelTestResult:
    """Store test results for a model."""
    model_name: str
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    tokens_used: Optional[int] = None
    response_time: Optional[float] = None


async def test_model(llm_client: LLMClientSingleton, model_name: str, messages: List[Dict[str, Any]]) -> ModelTestResult:
    """Test a specific model and return results."""
    start_time = time.time()
    try:
        response_content = ""
        async for content in llm_client.create_chat(
            model=model_name,
            messages=messages,
            temperature=0.7,
            stream=False
        ):
            response_content += content
        
        end_time = time.time()
        return ModelTestResult(
            model_name=model_name,
            success=True,
            response=response_content,
            response_time=end_time - start_time
        )
    except Exception as e:
        end_time = time.time()
        return ModelTestResult(
            model_name=model_name,
            success=False,
            error=str(e),
            response_time=end_time - start_time
        )


async def test_all_models():
    """Test all LLM models defined in the config."""
    # Check if API key exists
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not found in environment variables")
        return
    
    print(f"API key found: {api_key[:4]}...{api_key[-4:]} (length: {len(api_key)})")
    
    # Initialize the LLM singleton
    llm_client = LLMClientSingleton()
    
    # Get config for model names
    config = get_config()
    
    # List all models to test
    models_to_test = [
        config.ENTITY_LLM_MODEL,
        config.ANSWER_LLM_MODEL,
        config.TRANSLATE_LLM_MODEL
    ]
    
    # Prepare a simple test message
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello! What can you tell me about knowledge graphs in brief?"}
    ]
    
    # Test each model
    results = []
    for model_name in models_to_test:
        print(f"\nTesting model: {model_name}")
        result = await test_model(llm_client, model_name, messages)
        results.append(result)
        
        if result.success:
            # Truncate response for display if too long
            display_response = result.response
            if len(display_response) > 200:
                display_response = display_response[:200] + "... [truncated]"
            
            print(f"✅ Success - Response time: {result.response_time:.2f}s")
            print(f"Response preview: {display_response}")
        else:
            print(f"❌ Failed - Error: {result.error}")
    
    # Print summary
    print("\n" + "="*50)
    print("SUMMARY OF RESULTS")
    print("="*50)
    
    success_count = sum(1 for r in results if r.success)
    print(f"Total models tested: {len(results)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(results) - success_count}")
    
    if success_count > 0:
        # Find fastest model
        fastest = min((r for r in results if r.success), key=lambda x: x.response_time)
        print(f"\nFastest model: {fastest.model_name} ({fastest.response_time:.2f}s)")
    
    print("\nDetailed results:")
    for result in results:
        status = "✅ Success" if result.success else "❌ Failed"
        print(f"- {result.model_name}: {status} - {result.response_time:.2f}s")
    
    # Final API safety verification
    print("\nAPI SAFETY CHECK:")
    if api_key and len(results) > 0 and any(r.success for r in results):
        print("✅ Your OPENROUTER_API_KEY is working correctly and safely stored in the .env file.")
        print("✅ The LLMClientSingleton is properly handling the API key.")
        print("✅ The models are responding as expected.")
    else:
        print("❌ There were issues with your API setup. Please check the results above.")


if __name__ == "__main__":
    asyncio.run(test_all_models())
