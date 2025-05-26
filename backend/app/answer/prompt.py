"""Answer prompt utilities for SocioGraph.

This module provides prompt building functions for generating answers
from retrieved context, with support for citations and structured responses.
"""

from typing import List, Dict, Any
import re


def build_system_prompt() -> str:
    """Build the system prompt for answer generation."""
    return """You are a helpful research assistant that provides accurate, well-cited answers based on retrieved documents.

GUIDELINES:
1. Use ONLY the provided context to answer the question
2. If the answer isn't in the context, say "I don't have enough information to answer this question"
3. Include numbered citations [1], [2], etc. for each fact you reference
4. Structure your answer with clear paragraphs
5. Be concise but comprehensive
6. Use markdown formatting for better readability

CITATION FORMAT:
- Use [1], [2], [3] etc. for inline citations
- Each citation should correspond to a specific piece of information from the context
- Multiple citations can be used for the same sentence if drawing from multiple sources"""


def build_user_prompt(query: str, context_items: List[str]) -> str:
    """Build the user prompt with query and context."""
    # Build context with numbered references
    context_with_refs = []
    for i, item in enumerate(context_items, 1):
        context_with_refs.append(f"[{i}] {item}")
    
    context_str = "\n\n".join(context_with_refs)
    
    return f"""CONTEXT:
{context_str}

QUESTION: {query}

Please provide a well-structured answer with appropriate citations:"""


def attach_citations(answer_md: str, context_items: List[str]) -> str:
    """Post-process the answer to ensure proper citation formatting.
    
    This function validates that citations in the answer correspond to
    available context items and fixes any formatting issues.
    """
    # Find all citation patterns in the answer
    citation_pattern = r'\[(\d+)\]'
    citations = re.findall(citation_pattern, answer_md)
    
    # Convert to integers and get unique citations
    unique_citations = sorted(set(int(c) for c in citations if c.isdigit()))
    
    # Validate citations don't exceed available context
    max_available = len(context_items)
    valid_citations = [c for c in unique_citations if 1 <= c <= max_available]
    
    # If we have invalid citations, add a note
    invalid_citations = [c for c in unique_citations if c > max_available]
    if invalid_citations:
        answer_md += f"\n\n*Note: Some citations ({invalid_citations}) refer to unavailable sources and have been omitted.*"
    
    # Ensure proper citation formatting (superscript-style)
    answer_md = re.sub(r'\[(\d+)\]', r'<sup>[\1]</sup>', answer_md)
    
    return answer_md


def build_context_summary(context_items: List[str]) -> str:
    """Build a summary of the context for logging purposes."""
    if not context_items:
        return "No context available"
    
    total_chars = sum(len(item) for item in context_items)
    return f"{len(context_items)} context items, {total_chars} total characters"
