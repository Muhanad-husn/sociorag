"""Answer prompt utilities for SocioGraph.

This module provides prompt building functions for generating answers
from retrieved context, with support for source quotes and structured responses.
"""

from typing import List, Dict, Any
import re


def build_system_prompt() -> str:
    """Build the system prompt for answer generation."""
    return """You are a helpful research assistant that provides accurate, well-sourced answers based on retrieved documents.

GUIDELINES:
1. Start your response with a concise, descriptive title on the first line
2. Use ONLY the provided context to answer the question
3. If the answer isn't in the context, say "I don't have enough information to answer this question"
4. When referencing information, use direct quotes from the context
5. Structure your answer with clear paragraphs
6. Be concise but comprehensive
7. Use markdown formatting for better readability

RESPONSE FORMAT:
- First line: A concise title that summarizes the main topic or answer
- Second line: Leave blank
- Following lines: Your detailed answer with quotes

QUOTE FORMAT:
- Use direct quotes from the context: "quoted text" 
- Use partial quotes when appropriate to maintain readability
"""


def build_user_prompt(query: str, context_items: List[str]) -> str:
    """Build the user prompt with query and context."""
    # Build context without source identifiers
    context_str = "\n\n".join(context_items)
    
    return f"""CONTEXT:
{context_str}

QUESTION: {query}

Please provide a well-structured answer with a concise title, using direct quotes:"""


def process_quotes(answer_md: str, context_items: List[str]) -> str:
    """Post-process the answer to ensure proper quote formatting.
    
    This function validates and cleans up quote formatting in the answer.
    """
    # Since we no longer use source identifiers, we can simply return the answer
    # with any basic formatting cleanup if needed
    return answer_md.strip()


def build_context_summary(context_items: List[str]) -> str:
    """Build a summary of the context for logging purposes."""
    if not context_items:
        return "No context available"
    
    total_chars = sum(len(item) for item in context_items)
    return f"{len(context_items)} context items, {total_chars} total characters"


def extract_title_and_content(answer_md: str) -> tuple[str, str]:
    """Extract title and content from the generated answer.
    
    Returns a tuple of (title, content) where title is the first line
    and content is the rest of the answer.
    """
    lines = answer_md.strip().split('\n')
    
    if not lines:
        return "Untitled Answer", ""
    
    title = lines[0].strip()
    
    # If title starts with markdown header, clean it up
    if title.startswith('#'):
        title = title.lstrip('#').strip()
    
    # Get the content (skip empty lines after title)
    content_lines = []
    start_content = False
    
    for line in lines[1:]:
        if not start_content and line.strip() == "":
            continue  # Skip empty lines after title
        start_content = True
        content_lines.append(line)
    
    content = '\n'.join(content_lines).strip()
    
    return title, content


def sanitize_filename(title: str, max_length: int = 100) -> str:
    """Sanitize a title for use as a filename.
    
    Args:
        title: The title to sanitize
        max_length: Maximum length of the resulting filename
        
    Returns:
        A safe filename string
    """
    if not title or not title.strip():
        return "untitled_answer"
    
    # Remove markdown headers first
    title = title.strip()
    if title.startswith('#'):
        title = title.lstrip('#').strip()
    
    # Remove or replace unsafe characters (including more characters)
    filename = re.sub(r'[<>:"/\\|?*&]', '_', title)
    
    # Replace multiple spaces/underscores with single underscore
    filename = re.sub(r'[\s_]+', '_', filename)
    
    # Remove leading/trailing underscores and dots
    filename = filename.strip('_.')
    
    # Truncate if too long
    if len(filename) > max_length:
        filename = filename[:max_length].rstrip('_.')
    
    # Ensure it's not empty after sanitization
    if not filename:
        return "untitled_answer"
    
    return filename
