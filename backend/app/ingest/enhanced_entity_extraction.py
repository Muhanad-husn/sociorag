"""Enhanced entity extraction module for SocioGraph ingestion pipeline.

This module provides advanced entity extraction functionality with:
- Robust JSON parsing with multiple fallback strategies
- Retry mechanism for failed API calls
- Response caching to avoid duplicate API calls
- Batch processing for better efficiency
- Structured error reporting
"""

import re
import json
import time
import asyncio
import hashlib
from typing import List, Dict, Any, Tuple, Optional, Set, Union
from functools import lru_cache

from backend.app.core.config import get_config
from backend.app.core.singletons import get_logger, get_llm_client
from backend.app.prompts import graph_prompts as gp

config = get_config()
logger = get_logger()

# Global cache for storing API responses to avoid redundant calls
_response_cache = {}


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
    else:
        # If no array found, try to wrap content in square brackets
        # This handles cases where the model returns single objects without array
        if response.strip().startswith('{') and response.strip().endswith('}'):
            response = f"[{response}]"
    
    # Step 3: Fix common JSON syntax errors
    # Fix missing quotes around keys
    response = re.sub(r'(?<=[{,])\s*(\w+):', r'"\1":', response)
    
    # Fix trailing commas in arrays/objects
    response = re.sub(r',\s*([}\]])', r'\1', response)
    
    # Fix missing commas between objects in arrays
    response = re.sub(r'}(\s*){', r'},\1{', response)
    
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


def validate_entity_object(obj: Dict[str, Any]) -> Tuple[bool, Optional[Set[str]]]:
    """Validate that an entity object has all required fields.
    
    Args:
        obj: The entity object to validate
        
    Returns:
        Tuple of (is_valid, missing_fields_set)
    """
    required_fields = ["head", "head_type", "relation", "tail", "tail_type"]
    missing_fields = {field for field in required_fields if field not in obj}
    
    is_valid = len(missing_fields) == 0
    return is_valid, (None if is_valid else missing_fields)


def safe_parse_json(json_str: str) -> Tuple[List[Dict[str, str]], bool, Dict[str, Any]]:
    """Safely parse JSON, with fallback strategies for malformed JSON.
    
    Args:
        json_str: JSON string to parse
        
    Returns:
        Tuple of (parsed_data, success_flag, debug_info)
    """
    debug_info = {
        "parsing_attempts": 0,
        "errors": [],
        "strategy_used": None,
        "original_entity_count": 0,
        "valid_entity_count": 0
    }
    
    # First try: standard JSON parsing
    debug_info["parsing_attempts"] += 1
    try:
        data = json.loads(json_str)
        if isinstance(data, list):
            debug_info["original_entity_count"] = len(data)
            # Validate each object in the list
            valid_objects = []
            for i, obj in enumerate(data):
                is_valid, missing_fields = validate_entity_object(obj)
                if is_valid:
                    valid_objects.append(obj)
                else:
                    debug_info["errors"].append(f"Object {i} missing fields: {missing_fields}")
            
            debug_info["valid_entity_count"] = len(valid_objects)
            if valid_objects:
                debug_info["strategy_used"] = "standard_json_parsing"
                return valid_objects, True, debug_info
        else:
            debug_info["errors"].append(f"Parsed JSON is not a list but a {type(data)}")
    except json.JSONDecodeError as e:
        debug_info["errors"].append(f"Standard JSON parsing failed: {str(e)}")
    
    # Second try: repair and parse line by line
    debug_info["parsing_attempts"] += 1
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
                is_valid, missing_fields = validate_entity_object(obj)
                if is_valid:
                    valid_objects.append(obj)
                else:
                    debug_info["errors"].append(f"Object {i} missing fields: {missing_fields}")
            except json.JSONDecodeError as e:
                debug_info["errors"].append(f"Failed to parse object {i}: {str(e)}")
        
        if valid_objects:
            debug_info["strategy_used"] = "object_by_object_parsing"
            debug_info["valid_entity_count"] = len(valid_objects)
            return valid_objects, True, debug_info
    except Exception as e:
        debug_info["errors"].append(f"Object-by-object parsing failed: {str(e)}")
    
    # Third try: Try more aggressive extraction of JSON-like structures
    debug_info["parsing_attempts"] += 1
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
                is_valid, missing_fields = validate_entity_object(obj)
                if is_valid:
                    valid_objects.append(obj)
                else:
                    debug_info["errors"].append(f"Extracted object {i} missing fields: {missing_fields}")
            except json.JSONDecodeError as e:
                debug_info["errors"].append(f"Failed to parse extracted object {i}: {str(e)}")
        
        if valid_objects:
            debug_info["strategy_used"] = "aggressive_extraction"
            debug_info["valid_entity_count"] = len(valid_objects)
            return valid_objects, True, debug_info
    except Exception as e:
        debug_info["errors"].append(f"Aggressive extraction failed: {str(e)}")
    
    # Fourth try: Most aggressive JSON repair (new approach)
    debug_info["parsing_attempts"] += 1
    try:
        # Try using a JSON repair library if available
        try:
            import json_repair
            repaired = json_repair.repair_json(json_str)
            data = json.loads(repaired)
            
            if isinstance(data, list):
                valid_objects = [obj for obj in data if validate_entity_object(obj)[0]]
                if valid_objects:
                    debug_info["strategy_used"] = "json_repair_library"
                    debug_info["valid_entity_count"] = len(valid_objects)
                    return valid_objects, True, debug_info
        except ImportError:
            # Custom aggressive repair as fallback
            # This approach tries to reconstruct a valid JSON array by fixing common issues
            # like missing commas, unquoted strings, and malformed objects
            
            # Extract all property:value pairs that look like they might be part of an entity
            entity_props = re.findall(r'"(\w+)"\s*:\s*"([^"]*)"', json_str)
            
            # Group them into potential entities
            current_entity = {}
            entities = []
            
            for prop, value in entity_props:
                if prop in ["head", "head_type", "relation", "tail", "tail_type"]:
                    if prop == "head" and current_entity and "head" in current_entity:
                        # If we see "head" again, it's a new entity
                        entities.append(current_entity)
                        current_entity = {}
                    
                    current_entity[prop] = value
            
            # Don't forget the last entity
            if current_entity:
                entities.append(current_entity)
            
            # Validate and collect valid entities
            valid_objects = []
            for i, entity in enumerate(entities):
                is_valid, missing_fields = validate_entity_object(entity)
                if is_valid:
                    valid_objects.append(entity)
                else:
                    debug_info["errors"].append(f"Reconstructed entity {i} missing fields: {missing_fields}")
            
            if valid_objects:
                debug_info["strategy_used"] = "custom_reconstruction"
                debug_info["valid_entity_count"] = len(valid_objects)
                return valid_objects, True, debug_info
    except Exception as e:
        debug_info["errors"].append(f"Most aggressive JSON repair failed: {str(e)}")
    
    # If all parsing attempts fail, return empty list
    return [], False, debug_info


def get_cache_key(text: str) -> str:
    """Generate a cache key for a text chunk.
    
    Args:
        text: The text chunk
    
    Returns:
        Cache key as a string
    """
    # Use a hash of the text as the cache key
    return hashlib.md5(text.encode('utf-8')).hexdigest()


async def extract_entities_with_retry(text: str, max_retries: int = 3, 
                                     retry_delay: float = 2.0) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
    """Extract entities with retry mechanism.
    
    Args:
        text: Text to extract entities from
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
    
    Returns:
        Tuple of (entity_list, debug_info)
    """
    debug_info = {
        "attempts": 0,
        "success": False,
        "from_cache": False,
        "parsing_info": None,
        "error": None
    }
    
    # Check cache first
    cache_key = get_cache_key(text)
    if cache_key in _response_cache:
        logger.info(f"Using cached response for text chunk")
        debug_info["from_cache"] = True
        return _response_cache[cache_key], debug_info
    
    # Get LLM client
    client = get_llm_client()
    
    # Prepare the prompt
    prompt = [
        {"role": "system", "content": gp.SYSTEM_PROMPT},
        {"role": "user", "content": gp.USER_PROMPT_TEMPLATE.format(text=text)}
    ]
    
    # Retry loop
    for attempt in range(max_retries):
        debug_info["attempts"] += 1
        
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
                logger.warning(f"No content extracted from response (attempt {attempt+1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    debug_info["error"] = "No content extracted from response after all attempts"
                    return [], debug_info
            
            # Process with improved JSON parsing pipeline
            cleaned_json = clean_json_response(json_line)
            rows, success, parsing_info = safe_parse_json(cleaned_json)
            
            debug_info["parsing_info"] = parsing_info
            
            if success:
                logger.info(f"Successfully parsed JSON with {len(rows)} entities (attempt {attempt+1})")
                debug_info["success"] = True
                
                # Cache the successful result
                _response_cache[cache_key] = rows
                
                return rows, debug_info
            else:
                logger.warning(f"Parsing failed on attempt {attempt+1}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    debug_info["error"] = "All parsing attempts failed after all retry attempts"
                    return [], debug_info
                
        except Exception as e:
            logger.error(f"Error in extract_entities_with_retry (attempt {attempt+1}): {e}")
            debug_info["error"] = str(e)
            
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                continue
            else:
                return [], debug_info
    
    # This should not be reached due to the return in the loop, but just in case
    return [], debug_info


async def extract_entities_from_text(text: str) -> List[Dict[str, str]]:
    """Extract entities and relationships from a text chunk.
    
    This function uses the LLM to extract entities and relationships from
    a chunk of text, with robust JSON parsing and retry mechanism.
    
    Args:
        text: The text chunk to extract entities from
        
    Returns:
        List of entity relationship objects
    """
    entities, debug_info = await extract_entities_with_retry(text)
    return entities


async def batch_process_chunks(chunks: List[str], batch_size: int = 3, 
                              concurrency_limit: int = 2) -> List[List[Dict[str, str]]]:
    """Process multiple chunks in batches with concurrency control.
    
    Args:
        chunks: List of text chunks to process
        batch_size: Number of chunks to process in each batch
        concurrency_limit: Maximum number of concurrent API calls
    
    Returns:
        List of lists of entity relationship objects
    """
    results = []
    
    # Process in batches to control memory usage
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1} ({len(batch)} chunks)")
        
        # Use semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrency_limit)
        
        async def process_with_semaphore(chunk):
            async with semaphore:
                return await extract_entities_from_text(chunk)
        
        # Process the batch concurrently
        tasks = [process_with_semaphore(chunk) for chunk in batch]
        batch_results = await asyncio.gather(*tasks)
        
        results.extend(batch_results)
    
    return results


def clear_cache() -> None:
    """Clear the entity extraction cache."""
    global _response_cache
    cache_size = len(_response_cache)
    _response_cache = {}
    logger.info(f"Cleared entity extraction cache ({cache_size} entries)")
