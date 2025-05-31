"""Centralized markdown to HTML rendering.

This module provides a single point for converting markdown to HTML,
eliminating redundant processing between API responses and PDF generation.
"""

import hashlib
import time
import re
from functools import lru_cache

import bleach
from bleach.css_sanitizer import CSSSanitizer
from markdown_it import MarkdownIt
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound
from backend.app.core.singletons import LoggerSingleton

_logger = LoggerSingleton().get()

# Define allowed HTML tags and attributes for sanitization
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'b', 'i', 'u', 'strike', 'del',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'dl', 'dt', 'dd',
    'blockquote', 'code', 'pre', 'kbd', 'samp', 'var',
    'a', 'img', 'hr', 'sup', 'sub',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'div', 'span'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'code': ['class'],
    'pre': ['class'],
    'div': ['class'],
    'span': ['class', 'style'],  # Allow style for syntax highlighting
    'th': ['align'],
    'td': ['align'],
    'table': ['class']
}

# CSS sanitizer for syntax highlighting styles
CSS_SANITIZER = CSSSanitizer(
    allowed_css_properties=['color', 'font-weight', 'font-style', 'text-decoration'],
    allowed_svg_properties=[]
)

# Create Pygments HTML formatter for syntax highlighting
_formatter = HtmlFormatter(
    style='default',
    noclasses=True,  # Use inline styles instead of CSS classes
    nowrap=True      # Don't wrap in <div> tags
)


def highlight_code(code: str, lang: str = '', attrs: str = '') -> str:
    """Highlight code using Pygments.
    
    Args:
        code: The code to highlight
        lang: The language identifier (optional)
        attrs: Additional attributes (unused but required for markdown-it compatibility)
        
    Returns:
        HTML with syntax highlighting
    """
    try:
        _logger.debug(f"Highlighting code: lang='{lang}', code_length={len(code)}")
        
        if lang:
            # Try to get lexer by language name
            lexer = get_lexer_by_name(lang, stripall=True)
        else:
            # Try to guess the language
            lexer = guess_lexer(code)
            
        highlighted = highlight(code, lexer, _formatter)
        _logger.debug(f"Highlighted result length: {len(highlighted)}")
        return highlighted
        
    except ClassNotFound:
        # Fallback to plain code block if language not recognized
        _logger.debug(f"Language '{lang}' not recognized for syntax highlighting")
        return bleach.clean(code, tags=[], attributes={})
    except Exception as e:
        _logger.error(f"Error highlighting code: {e}")
        return bleach.clean(code, tags=[], attributes={})

def post_process_syntax_highlighting(html: str) -> str:
    """Post-process HTML to apply syntax highlighting to code blocks.
    
    Args:
        html: HTML content with <code class="language-*"> blocks
        
    Returns:
        HTML with syntax highlighting applied
    """
    def replace_code_block(match):
        lang = match.group(1) if match.group(1) else ''
        code_content = match.group(2)
        
        # Decode HTML entities in the code content
        code_content = code_content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"')
        
        try:
            if lang:
                lexer = get_lexer_by_name(lang, stripall=True)
            else:
                lexer = guess_lexer(code_content)
                
            highlighted = highlight(code_content, lexer, _formatter)
            return f'<pre><code class="language-{lang}">{highlighted}</code></pre>'
            
        except ClassNotFound:
            _logger.debug(f"Language '{lang}' not recognized for syntax highlighting")
            return match.group(0)  # Return original
        except Exception as e:
            _logger.error(f"Error highlighting code: {e}")
            return match.group(0)  # Return original
    
    # Pattern to match <pre><code class="language-*">...</code></pre> blocks
    pattern = r'<pre><code class="language-([^"]*)">(.*?)</code></pre>'
    return re.sub(pattern, replace_code_block, html, flags=re.DOTALL)


# Initialize markdown parser with preset configuration
_md = MarkdownIt("default", {
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
        # Render markdown to HTML
        html = _md.render(markdown_content)
        
        # Apply syntax highlighting to code blocks
        html = post_process_syntax_highlighting(html)
        
        return html
    except Exception as e:
        _logger.error(f"Error rendering markdown to HTML: {e}")
        # Return the original content wrapped in a basic paragraph if rendering fails
        return f"<p>{markdown_content}</p>"


def render_markdown_to_html_safe(markdown_content: str) -> str:
    """Convert markdown content to sanitized HTML.
    
    This function provides an additional security layer by sanitizing
    the HTML output to prevent potential XSS attacks.
    
    Args:
        markdown_content: The markdown string to convert
        
    Returns:
        The sanitized HTML string
    """
    try:
        # First render markdown to HTML
        html = _md.render(markdown_content)
          # Apply syntax highlighting to code blocks
        html = post_process_syntax_highlighting(html)
        
        # Then sanitize the HTML - allow style attribute for syntax highlighting
        sanitized_html = bleach.clean(
            html, 
            tags=ALLOWED_TAGS, 
            attributes=ALLOWED_ATTRIBUTES,
            css_sanitizer=CSS_SANITIZER,  # Allow safe CSS properties
            strip=True  # Remove disallowed tags instead of escaping
        )
        
        # Additional security: remove any remaining javascript: references in text content
        sanitized_html = re.sub(r'javascript:', '', sanitized_html, flags=re.IGNORECASE)
        
        return sanitized_html
    except Exception as e:
        _logger.error(f"Error rendering markdown to sanitized HTML: {e}")
        # Return the original content wrapped in a basic paragraph if rendering fails
        return f"<p>{bleach.clean(markdown_content, tags=[], attributes={}, strip=True)}</p>"


@lru_cache(maxsize=1000)
def _render_markdown_cached(content_hash: str, markdown_content: str) -> str:
    """Cached version of markdown rendering (internal use only)."""
    return render_markdown_to_html(markdown_content)


@lru_cache(maxsize=1000) 
def _render_markdown_safe_cached(content_hash: str, markdown_content: str) -> str:
    """Cached version of safe markdown rendering (internal use only)."""
    return render_markdown_to_html_safe(markdown_content)


def render_markdown_to_html_cached(markdown_content: str) -> str:
    """Render markdown with caching for better performance.
    
    Uses content hash as cache key to ensure cache invalidation
    when content changes.
    
    Args:
        markdown_content: The markdown string to convert
        
    Returns:
        The rendered HTML string
    """
    content_hash = hashlib.md5(markdown_content.encode('utf-8')).hexdigest()
    return _render_markdown_cached(content_hash, markdown_content)


def render_markdown_to_html_safe_cached(markdown_content: str) -> str:
    """Render markdown to sanitized HTML with caching.
    
    Args:
        markdown_content: The markdown string to convert
        
    Returns:
        The sanitized HTML string
    """
    content_hash = hashlib.md5(markdown_content.encode('utf-8')).hexdigest()
    return _render_markdown_safe_cached(content_hash, markdown_content)


def render_markdown_to_html_with_metrics(markdown_content: str) -> tuple[str, float]:
    """Render markdown and return HTML with timing metrics.
    
    Args:
        markdown_content: The markdown string to convert
        
    Returns:
        Tuple of (rendered_html, duration_seconds)
    """
    start_time = time.time()
    html = render_markdown_to_html(markdown_content)
    duration = time.time() - start_time
    
    _logger.debug(f"Markdown rendering took {duration:.3f}s for {len(markdown_content)} chars")
    return html, duration


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
