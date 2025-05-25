"""Entity extraction module for SocioGraph ingestion pipeline.

This module provides the improved entity extraction functionality with robust JSON parsing.
"""

import re
import json
from typing import List, Dict, Any, Tuple

from backend.app.core.config import get_config
from backend.app.core.singletons import get_logger, get_llm_client
from backend.app.prompts import graph_prompts as gp

config = get_config()
logger = get_logger()


def clean_json_response(raw_response: str) -> str:
    """Clean a JSON response from an LLM.
    
    This handles common issues like markdown code blocks, extra text,
    and malformed JSON to extract the best possible JSON content.
    
    Args:
        raw_response: The raw response from the LLM
        
    Returns:
        Cleaned JSON string ready for parsing
    """
    # Log raw response for debugging
    logger.debug(f"Raw LLM response: {raw_response}")
    
    # Step 1: Remove markdown code blocks
    # This handles ```json and ``` patterns
    response = re.sub(r'```(?:json)?\s*|\s*```', '', raw_response)
    
    # Step 2: Try to extract just the JSON array
    # Look for a pattern that starts with [ and ends with ]
    json_array_match = re.search(r'\[(.*)\]', response, re.DOTALL)
    if json_array_match:
        response = f"[{json_array_match.group(1)}]"
    
    # Step 3: Fix common JSON syntax errors
    # Fix missing quotes around keys
    response = re.sub(r'(?<=[{,])\s*(\w+):', r'"\1":', response)
    
    # Fix trailing commas in arrays/objects
    response = re.sub(r',\s*([}\]])', r'\1', response)
    
    # Step 4: Remove any non-JSON text before or after the array
    response = response.strip()
    if not (response.startswith('[') and response.endswith(']')):
        # If we don't have a clean JSON array, try to find one
        start = response.find('[')
        end = response.rfind(']')
        if start >= 0 and end > start:
            response = response[start:end+1]
    
    # Step 5: Final clean-up
    response = response.strip()
    
    logger.debug(f"Cleaned JSON: {response}")
    return response


def validate_entity_object(obj: Dict[str, Any]) -> bool:
    """Validate that an entity object has all required fields.
    
    Args:
        obj: The entity object to validate
        
    Returns:
        True if valid, False if not
    """
    required_fields = ["head", "head_type", "relation", "tail", "tail_type"]
    return all(field in obj for field in required_fields)


def safe_parse_json(json_str: str) -> Tuple[List[Dict[str, str]], bool]:
    """Safely parse JSON, with fallback strategies for malformed JSON.
    
    Args:
        json_str: JSON string to parse
        
    Returns:
        Tuple of (parsed_data, success_flag)
    """
    # First try: standard JSON parsing
    try:
        data = json.loads(json_str)
        if isinstance(data, list):
            # Validate each object in the list
            valid_objects = [obj for obj in data if validate_entity_object(obj)]
            if valid_objects:
                return valid_objects, True
    except json.JSONDecodeError:
        logger.warning(f"Standard JSON parsing failed")
    
    # Second try: repair and parse line by line
    # This handles cases where some objects are valid and some are not
    try:
        # Split by objects (looking for pattern like }, {)
        object_pattern = re.compile(r'},\s*{')
        parts = object_pattern.split(json_str.strip('[]'))
        
        # Repair and parse each object
        valid_objects = []
        for i, part in enumerate(parts):
            # Add opening/closing braces if needed
            if not part.startswith('{'):
                part = '{' + part
            if not part.endswith('}'):
                part = part + '}'
                
            try:
                obj = json.loads(part)
                if validate_entity_object(obj):
                    valid_objects.append(obj)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse object {i+1}")
        
        if valid_objects:
            return valid_objects, True
    except Exception as e:
        logger.warning(f"Object-by-object parsing failed: {e}")
    
    # Third try: Try more aggressive extraction of JSON-like structures
    try:
        # Look for patterns that resemble JSON objects
        object_matches = re.finditer(r'{[^{}]*"head"[^{}]*"tail"[^{}]*}', json_str)
        
        valid_objects = []
        for i, match in enumerate(object_matches):
            obj_str = match.group(0)
            
            # Try to fix common issues
            # Ensure property names are quoted
            obj_str = re.sub(r'(\w+):', r'"\1":', obj_str)
            # Remove trailing commas
            obj_str = re.sub(r',\s*}', '}', obj_str)
            
            try:
                obj = json.loads(obj_str)
                if validate_entity_object(obj):
                    valid_objects.append(obj)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse extracted object {i+1}")
        
        if valid_objects:
            return valid_objects, True
    except Exception as e:
        logger.warning(f"Aggressive extraction failed: {e}")
    
    # If all parsing attempts fail, return empty list
    return [], False


async def extract_entities_from_text(text: str) -> List[Dict[str, str]]:
    """Extract entities and relationships from a text chunk.
    
    This function uses the LLM to extract entities and relationships from
    a chunk of text, with robust JSON parsing.
    
    Args:
        text: The text chunk to extract entities from
        
    Returns:
        List of entity relationship objects
    """
    # Get LLM client
    client = get_llm_client()
    
    # Prepare the prompt
    prompt = [
        {"role": "system", "content": gp.SYSTEM_PROMPT},
        {"role": "user", "content": gp.USER_PROMPT_TEMPLATE.format(text=text)}
    ]
    
    # Use non-streaming for better reliability
    try:
        # Import here to avoid circular imports
        from openrouter.client import create_chat_completion
        from openrouter.models.request import ChatCompletionRequest
        
        # Create request with simple dict messages
        request_data = {
            "model": config.ENTITY_LLM_MODEL,
            "messages": prompt,
            "temperature": 0.3,
            "stream": False,
            "max_tokens": 1000
        }
        
        # Create request and get response
        request = ChatCompletionRequest(**request_data)
        response = await create_chat_completion(request)
        
        # Extract content from response
        json_line = ""
        if hasattr(response, 'choices') and response.choices:
            choice = response.choices[0]
            if hasattr(choice, 'message') and choice.message:
                content = getattr(choice.message, 'content', None)
                if content:
                    json_line = content
        
        if not json_line:
            logger.warning("No content extracted from response")
            return []
        
        # Process with improved JSON parsing pipeline
        cleaned_json = clean_json_response(json_line)
        rows, success = safe_parse_json(cleaned_json)
        
        if success:
            logger.info(f"Successfully parsed JSON with {len(rows)} entities")
            return rows
        else:
            logger.warning("All parsing attempts failed")
            return []
            
    except Exception as e:
        logger.error(f"Error in extract_entities_from_text: {e}")
        return []
