"""PDF generation from markdown answers.

This module converts markdown answers to styled PDF documents using WeasyPrint.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from markdown_it import MarkdownIt

from backend.app.core.config import get_config
from backend.app.core.singletons import LoggerSingleton

_cfg = get_config()
_logger = LoggerSingleton().get()

# Import standard libraries
import sys
import logging
import warnings
# os is already imported at the top of the file

# WeasyPrint import with proper FontConfiguration handling
WEASYPRINT_AVAILABLE = False
FONT_CONFIG_AVAILABLE = False

# Suppress the Fontconfig warnings on Windows
# These warnings are common on Windows and don't affect functionality
if sys.platform.startswith('win'):
    # Create fonts directory if it doesn't exist
    fonts_dir = _cfg.BASE_DIR / 'resources' / 'fonts'
    fonts_dir.mkdir(parents=True, exist_ok=True)
    
    # Set environment variables for fontconfig
    os.environ['FONTCONFIG_PATH'] = str(fonts_dir)
    os.environ['FONTCONFIG_FILE'] = str(fonts_dir / 'fonts.conf')
    
    # Set log level for weasyprint to ERROR to suppress warnings
    logging.getLogger('weasyprint').setLevel(logging.ERROR)

# Import WeasyPrint and its components
try:
    from weasyprint import HTML, CSS, __version__ as weasyprint_version
    WEASYPRINT_AVAILABLE = True
    
    # Log the WeasyPrint version being used
    _logger.info(f"Using WeasyPrint version: {weasyprint_version}")
    
    # Check if we're using the expected version (from requirements.txt)
    expected_version = "65.1"
    if weasyprint_version != expected_version:
        _logger.warning(f"WeasyPrint version mismatch: using {weasyprint_version}, expected {expected_version}")

    # Import FontConfiguration from the correct location in WeasyPrint 65.1
    from weasyprint.text.fonts import FontConfiguration
    FONT_CONFIG_AVAILABLE = True
    _logger.info("WeasyPrint and FontConfiguration successfully imported")
except Exception as e:
    _logger.error(f"Failed to import WeasyPrint or FontConfiguration: {e}")

# Log success status
if WEASYPRINT_AVAILABLE and FONT_CONFIG_AVAILABLE:
    _logger.info("PDF generation is fully available")
elif WEASYPRINT_AVAILABLE:
    _logger.warning("PDF generation available but without FontConfiguration support")
    

# Initialize markdown parser with common features
_md = MarkdownIt("commonmark", {
    "html": True,         # Allow HTML tags
    "linkify": True,      # Auto-convert URLs to links
    "typographer": True   # Smart quotes, dashes, etc.
})


def _ensure_saved_dir() -> Path:
    """Ensure the saved directory exists."""
    saved_dir = _cfg.SAVED_DIR
    saved_dir.mkdir(parents=True, exist_ok=True)
    return saved_dir


def _get_resource_path(resource_name: str) -> Path:
    """Get the absolute path to a resource.
    
    Args:
        resource_name: The name of the resource file
        
    Returns:
        Path to the resource file
    """
    resource_dir = _cfg.BASE_DIR / "resources"
    return resource_dir / resource_name


def _build_html_document(answer_md: str, query: str) -> str:
    """Build a complete HTML document from markdown content."""
    # Convert markdown to HTML
    html_body = _md.render(answer_md)
    
    # Create timestamp for the document
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Build complete HTML document with metadata
    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SocioGraph Answer - {query[:50]}...</title>
    <meta name="generator" content="SocioGraph">
    <meta name="created" content="{timestamp}">
    <style>
        body {{
            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.5;
            margin: 2cm;
        }}
        img {{
            max-width: 100%;
            height: auto;
        }}
        pre, code {{
            background: #f5f5f5;
            padding: 0.2em 0.4em;
            border-radius: 3px;
            font-family: 'Courier New', Courier, monospace;
        }}
        pre code {{
            padding: 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
        }}
        th {{
            background-color: #f2f2f2;
        }}
    </style>
</head>
<body>
    <header>
        <h1>SocioGraph Answer</h1>
        <div class="query-info">
            <strong>Query:</strong> {query}
        </div>
        <div class="timestamp">
            <strong>Generated:</strong> {timestamp}
        </div>
        <hr>
    </header>
    
    <main>
        {html_body}
    </main>
    
    <footer>
        <hr>
        <p><em>Generated by SocioGraph - AI-powered document analysis and knowledge graph</em></p>
    </footer>
</body>
</html>"""
    
    return html_doc


def _process_embedded_resources(html_content: str) -> str:
    """Process and embed resources (images, etc.) in the HTML content.
    
    Args:
        html_content: The HTML content to process
        
    Returns:
        Processed HTML content with properly handled resources
    """
    # Currently just a placeholder for future image handling
    # This function could be expanded to handle data URIs, local images, etc.
    
    # Basic support for making image paths absolute if they're relative
    # This helps WeasyPrint locate images properly
    base_url = str(_cfg.BASE_DIR)
    
    # Simple handling for relative image paths
    # This doesn't cover all cases but handles basic scenarios
    img_pattern = 'src="'
    if base_url and img_pattern in html_content:
        for img_src in html_content.split(img_pattern)[1:]:
            end_quote = img_src.find('"')
            if end_quote != -1:
                src = img_src[:end_quote]
                # Only process relative paths (not URLs or data URIs)
                if src and not src.startswith(('http://', 'https://', 'data:')):
                    # Make relative path absolute for proper resolution
                    full_path = f"{base_url}/{src}" if not src.startswith('/') else f"{base_url}{src}"
                    html_content = html_content.replace(f'src="{src}"', f'src="{full_path}"')
    
    return html_content


def save_pdf(answer_md: str, query: str, filename: Optional[str] = None) -> Path:
    """Save a markdown answer as a styled PDF.
    
    Args:
        answer_md: The markdown content to convert
        query: The original query (used for metadata)
        filename: Optional custom filename (without extension)
        
    Returns:
        Path to the saved PDF file
    """
    _logger.info(f"Starting PDF generation for query: {query[:100]}...")
    
    if not WEASYPRINT_AVAILABLE:
        # Fallback: save as HTML file instead of PDF
        _logger.warning("WeasyPrint not available - saving as HTML instead of PDF")
        return _save_as_html(answer_md, query, filename)
    
    try:
        # Ensure output directory exists
        saved_dir = _ensure_saved_dir()
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"answer_{timestamp}"
        
        # Ensure .pdf extension
        if not filename.endswith('.pdf'):
            filename = f"{filename}.pdf"
            
        output_path = saved_dir / filename
        
        # Build HTML document
        html_content = _build_html_document(answer_md, query)
        
        # Process any embedded resources
        html_content = _process_embedded_resources(html_content)
          # Check if CSS theme file exists
        css_path = _cfg.PDF_THEME
        stylesheets = []
        
        if not css_path.exists():
            _logger.warning(f"PDF theme CSS not found at {css_path}, using default styling")
        else:
            try:
                stylesheets.append(CSS(str(css_path)))
                _logger.debug(f"Added custom CSS theme from {css_path}")
            except Exception as css_error:
                _logger.warning(f"Error loading custom CSS theme: {css_error}, using default styling")
            
        # Add custom page size and margin control
        page_css = CSS(string='''
            @page {
                size: letter;
                margin: 2cm;
                @top-center {
                    content: "SocioGraph";
                    font-size: 9pt;
                    color: #666;
                }
                @bottom-center {
                    content: "Page " counter(page) " of " counter(pages);
                    font-size: 9pt;
                }
            }
        ''')
        stylesheets = [page_css] + stylesheets
        
        # Generate PDF
        _logger.info(f"Rendering PDF to {output_path}")
        
        # Create HTML document with proper base URL for resource resolution
        html_doc = HTML(
            string=html_content, 
            base_url=str(_cfg.BASE_DIR)
        )
          # Write PDF with font configuration if available
        if FONT_CONFIG_AVAILABLE:
            try:
                # Create a font configuration with better error handling
                font_config = FontConfiguration()
                
                # Check for fonts directory and create if it doesn't exist
                fonts_dir = _cfg.BASE_DIR / "resources" / "fonts"
                fonts_dir.mkdir(parents=True, exist_ok=True)
                
                # Log font configuration info for debugging
                _logger.debug(f"Using font configuration with fonts directory: {fonts_dir}")
                  # Generate PDF with font configuration
                html_doc.write_pdf(
                    str(output_path), 
                    stylesheets=stylesheets,
                    font_config=font_config,
                    optimize_size=('fonts', 'images'),  # Optimize PDF size
                    presentational_hints=True  # Use HTML presentational hints
                )
            except Exception as font_error:
                _logger.warning(f"Error with font configuration: {font_error}, falling back to default")
                # Fall back to default if font configuration fails
                html_doc.write_pdf(
                    str(output_path), 
                    stylesheets=stylesheets,
                    optimize_size=('fonts', 'images'),  # Still optimize even in fallback
                    presentational_hints=True
                )
        else:
            html_doc.write_pdf(
                str(output_path), 
                stylesheets=stylesheets,
                optimize_size=('fonts', 'images'),
                presentational_hints=True
            )
        
        # Verify file was created
        if output_path.exists():
            file_size = output_path.stat().st_size
            _logger.info(f"PDF successfully created: {output_path} ({file_size} bytes)")
            return output_path
        else:
            raise RuntimeError("PDF file was not created")
            
    except Exception as e:
        _logger.error(f"Error generating PDF: {e}")
        
        # Log more specific error information for WeasyPrint-related issues
        if "weasyprint" in str(e).lower():
            _logger.error("This appears to be a WeasyPrint-specific error. Check font dependencies or CSS compatibility.")
        elif "css" in str(e).lower():
            _logger.error("This appears to be a CSS-related error. Check your CSS styling.")
        
        # Fall back to HTML
        _logger.info("Falling back to HTML format...")
        return _save_as_html(answer_md, query, filename)


def _save_as_html(answer_md: str, query: str, filename: Optional[str] = None) -> Path:
    """Fallback function to save as HTML when PDF generation is not available."""
    saved_dir = _ensure_saved_dir()
    
    # Generate filename if not provided
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"answer_{timestamp}"
    
    # Use .html extension for fallback
    if filename.endswith('.pdf'):
        filename = filename[:-4] + '.html'
    elif not filename.endswith('.html'):
        filename = f"{filename}.html"
        
    output_path = saved_dir / filename
    
    # Build HTML document
    html_content = _build_html_document(answer_md, query)
    
    # Write HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    _logger.info(f"HTML file created: {output_path}")
    return output_path


def check_weasyprint_environment() -> dict:
    """Check the environment for WeasyPrint configuration.
    
    Returns:
        Dictionary with environment information for diagnostics
    """
    env_info = {
        "weasyprint_available": WEASYPRINT_AVAILABLE,
        "fontconfig_available": FONT_CONFIG_AVAILABLE,
        "platform": sys.platform,
    }
    
    if WEASYPRINT_AVAILABLE:
        env_info["weasyprint_version"] = weasyprint_version
        
        # Check for key directories
        fonts_dir = _cfg.BASE_DIR / 'resources' / 'fonts'
        env_info["fonts_dir_exists"] = fonts_dir.exists()
        
        if fonts_dir.exists():
            env_info["fonts_conf_exists"] = (fonts_dir / 'fonts.conf').exists()
        
        # Check environment variables
        env_info["fontconfig_path"] = os.environ.get('FONTCONFIG_PATH', 'Not set')
        env_info["fontconfig_file"] = os.environ.get('FONTCONFIG_FILE', 'Not set')
        
        # Check if we can create a FontConfiguration instance
        if FONT_CONFIG_AVAILABLE:
            try:
                FontConfiguration()
                env_info["fontconfig_init_success"] = True
            except Exception as e:
                env_info["fontconfig_init_success"] = False
                env_info["fontconfig_init_error"] = str(e)
    
    return env_info


def get_pdf_url(pdf_path: Path) -> str:
    """Generate a URL for accessing a saved PDF.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Relative URL for accessing the PDF
    """
    # Get relative path from saved directory
    try:
        relative_path = pdf_path.relative_to(_cfg.SAVED_DIR)
        return f"/static/saved/{relative_path}"
    except ValueError:
        # If path is not relative to saved dir, use just the filename
        return f"/static/saved/{pdf_path.name}"
