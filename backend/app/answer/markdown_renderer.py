"""Centralized markdown to HTML rendering.

This module provides a single point for converting markdown to HTML,
eliminating redundant processing between API responses and PDF generation.
"""

from markdown_it import MarkdownIt
from backend.app.core.singletons import LoggerSingleton

_logger = LoggerSingleton().get()

# Initialize markdown parser with common features
_md = MarkdownIt("commonmark", {
    "html": True,         # Allow HTML tags
    "linkify": True,      # Auto-convert URLs to links
    "typographer": True   # Smart quotes, dashes, etc.
})


def render_markdown_to_html(markdown_content: str) -> str:
    """Convert markdown content to HTML.
    
    Args:
        markdown_content: The markdown string to convert
        
    Returns:
        The rendered HTML string
    """
    try:
        return _md.render(markdown_content)
    except Exception as e:
        _logger.error(f"Error rendering markdown to HTML: {e}")
        # Return the original content wrapped in a basic paragraph if rendering fails
        return f"<p>{markdown_content}</p>"


def is_markdown_content(content: str) -> bool:
    """Check if content appears to be markdown.
    
    Args:
        content: The content string to check
        
    Returns:
        True if content appears to be markdown, False otherwise
    """
    # Basic heuristics to detect markdown
    markdown_indicators = [
        '# ',      # Headers
        '## ',     # Headers
        '### ',    # Headers
        '* ',      # Bullet lists
        '- ',      # Bullet lists
        '1. ',     # Numbered lists
        '**',      # Bold
        '__',      # Bold
        '*',       # Italic
        '_',       # Italic
        '`',       # Code
        '[',       # Links
        '```',     # Code blocks
    ]
    
    return any(indicator in content for indicator in markdown_indicators)
