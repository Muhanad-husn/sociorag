"""Test the LLM singleton with the OPENROUTER_API_KEY."""

import asyncio
import os
from pprint import pprint

from app.core.singletons import LLMClientSingleton, get_config
from app.core.config import get_config


async def test_llm_singleton():
    """Test the LLM singleton with a simple query."""
    
    # Check if API key exists
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not found in environment variables")
        return
    
    print(f"API key found: {api_key[:4]}...{api_key[-4:]}")
    
    # Initialize the LLM singleton
    llm_client = LLMClientSingleton()
    
    # Get config for model names
    config = get_config()
    
    # Choose a model from config
    model = config.ENTITY_LLM_MODEL  # Using Gemini Flash
    print(f"Using model: {model}")
    
    # Prepare a simple test message
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello! What can you tell me about knowledge graphs in brief?"}
    ]
      # Test non-streaming response first
    print("\nTesting non-streaming response:")
    try:
        response_content = ""
        async for content in llm_client.create_chat(
            model=model,
            messages=messages,
            temperature=0.7,
            stream=False
        ):
            response_content += content
        
        print(f"Response:\n{response_content}")
    except Exception as e:
        print(f"Error with non-streaming: {str(e)}")
    
    # Let's check the model list from OpenRouter
    print("\nTesting with ANSWER_LLM_MODEL:")
    answer_model = config.ANSWER_LLM_MODEL
    print(f"Using model: {answer_model}")
    
    try:
        response_content = ""
        async for content in llm_client.create_chat(
            model=answer_model,
            messages=messages,
            temperature=0.7,
            stream=False
        ):
            response_content += content
        
        print(f"Response:\n{response_content}")
    except Exception as e:
        print(f"Error with ANSWER_LLM_MODEL: {str(e)}")
        
    # Check with TRANSLATE_LLM_MODEL
    print("\nTesting with TRANSLATE_LLM_MODEL:")
    translate_model = config.TRANSLATE_LLM_MODEL
    print(f"Using model: {translate_model}")
    
    try:
        response_content = ""
        async for content in llm_client.create_chat(
            model=translate_model,
            messages=messages,
            temperature=0.7,
            stream=False
        ):
            response_content += content
        
        print(f"Response:\n{response_content}")
    except Exception as e:
        print(f"Error with TRANSLATE_LLM_MODEL: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_llm_singleton())
