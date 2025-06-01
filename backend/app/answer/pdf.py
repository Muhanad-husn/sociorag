"""PDF generation from markdown answers.

This module converts markdown answers to styled PDF documents using Playwright.
Migrated from WeasyPrint for better performance and reduced resource usage.
"""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

from markdown_it import MarkdownIt
from playwright.sync_api import sync_playwright, Browser, Page
from playwright.async_api import async_playwright, Browser as AsyncBrowser, Page as AsyncPage

from backend.app.core.config import get_config
from backend.app.core.singletons import LoggerSingleton
from backend.app.answer.markdown_renderer import render_markdown_to_html

_cfg = get_config()
_logger = LoggerSingleton().get()

# Global variables for browser management
_browser: Optional[AsyncBrowser] = None
_sync_browser: Optional[Browser] = None
_playwright_initialized = False
_playwright_available = False

# Thread pool for sync operations
_thread_pool = ThreadPoolExecutor(max_workers=2)


async def _initialize_playwright():
    """Initialize Playwright and browser instances."""
    global _playwright_initialized, _playwright_available, _browser
    
    if _playwright_initialized:
        return
    
    _logger.info("Initializing Playwright for PDF generation...")
    start_time = time.time()
    try:        # Check if Playwright is available
        import playwright
        _playwright_available = True
        # Get version from package metadata instead of __version__
        try:
            import pkg_resources
            playwright_version = pkg_resources.get_distribution("playwright").version
            _logger.info(f"Playwright version: {playwright_version}")
        except (ImportError, pkg_resources.DistributionNotFound):
            _logger.info("Playwright installed (version detection unavailable)")
        
        # Initialize async browser for better performance
        playwright_instance = await async_playwright().start()
        _browser = await playwright_instance.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",  # For containerized environments
                "--disable-gpu",
                "--font-cache-shared",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",  # Overcome limited resource problems
                "--disable-extensions",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding"
            ]
        )
        
        _logger.info("Playwright browser initialized successfully")
        
    except ImportError as e:
        _logger.error(f"Playwright not installed: {e}")
        _playwright_available = False
    except Exception as e:
        _logger.error(f"Failed to initialize Playwright: {e}")
        _playwright_available = False
    
    duration = time.time() - start_time
    _logger.info(f"Playwright initialization completed in {duration:.2f}s")
    _playwright_initialized = True


def _initialize_sync_playwright():
    """Initialize synchronous Playwright browser for sync operations."""
    global _sync_browser
    
    if _sync_browser and _sync_browser.is_connected():
        return
    
    try:
        playwright_instance = sync_playwright().start()
        _sync_browser = playwright_instance.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-gpu",
                "--font-cache-shared",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-extensions"
            ]
        )
        _logger.info("Sync Playwright browser initialized")
    except Exception as e:
        _logger.error(f"Failed to initialize sync Playwright: {e}")


async def get_browser() -> AsyncBrowser:
    """Get the global async browser instance."""
    await _initialize_playwright()
    if not _browser or not _browser.is_connected():
        await _initialize_playwright()
    return _browser


def is_playwright_available() -> bool:
    """Check if Playwright is available for PDF generation."""
    global _playwright_available
    
    if not _playwright_available:
        # Try to import Playwright to check availability
        try:
            import playwright
            from playwright.sync_api import sync_playwright
            _playwright_available = True
        except ImportError:
            _playwright_available = False
    
    return _playwright_available


def _ensure_saved_dir() -> Path:
    """Ensure the saved directory exists."""
    saved_dir = _cfg.SAVED_DIR
    saved_dir.mkdir(parents=True, exist_ok=True)
    return saved_dir


def cleanup_old_saved_files(max_files: Optional[int] = None) -> int:
    """Remove old saved PDF files, keeping only the most recent ones.
    
    Args:
        max_files: Maximum number of files to keep (uses config default if None)
        
    Returns:
        Number of files removed
    """
    if max_files is None:
        max_files = _cfg.SAVED_LIMIT
        
    try:
        saved_dir = _ensure_saved_dir()
        
        # Get all PDF files in the saved directory
        pdf_files = []
        for file_path in saved_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() == '.pdf':
                try:
                    stat = file_path.stat()
                    pdf_files.append((file_path, stat.st_mtime))
                except (OSError, PermissionError):
                    # Skip files that can't be accessed
                    continue
        
        # Sort by modification time (newest first)
        pdf_files.sort(key=lambda x: x[1], reverse=True)
        
        if len(pdf_files) <= max_files:
            return 0  # Nothing to clean up
            
        # Keep only the most recent files, remove the rest
        files_to_remove = pdf_files[max_files:]
        removed_count = 0
        
        for file_path, _ in files_to_remove:
            try:
                file_path.unlink()  # Delete the file
                removed_count += 1
                _logger.debug(f"Removed old saved file: {file_path.name}")
            except (OSError, PermissionError) as e:
                _logger.warning(f"Could not remove file {file_path.name}: {e}")
                continue
                
        if removed_count > 0:
            _logger.info(f"Cleaned up {removed_count} old saved PDF files (kept {len(pdf_files) - removed_count} most recent)")
        
        return removed_count
        
    except Exception as e:
        _logger.error(f"Error cleaning up saved files: {e}")
        return 0


def _get_resource_path(resource_name: str) -> Path:
    """Get the absolute path to a resource.
    
    Args:
        resource_name: The name of the resource file
        
    Returns:
        Path to the resource file
    """
    resource_dir = _cfg.BASE_DIR / "resources"
    return resource_dir / resource_name


def _build_html_document(answer_md: str, query: str, language: str = "en") -> str:
    """Build a complete HTML document from markdown content with proper language and RTL support."""
    # Convert markdown to HTML using centralized renderer
    html_body = render_markdown_to_html(answer_md)
    
    # Create timestamp for the document
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Load custom CSS if available
    css_content = ""
    css_path = _cfg.BASE_DIR / "resources" / "pdf_theme.css"
    if css_path.exists():
        try:
            css_content = css_path.read_text(encoding="utf-8")
        except Exception as e:
            _logger.warning(f"Could not load CSS theme: {e}")
    
    # Determine text direction and RTL styles
    is_rtl = language == "ar"
    direction = "rtl" if is_rtl else "ltr"
    text_align = "right" if is_rtl else "left"
    
    # Additional RTL-specific CSS
    rtl_css = ""
    if is_rtl:
        rtl_css = """
        /* Arabic RTL-specific styles */
        body {
            font-family: 'Noto Sans Arabic', 'Arial Unicode MS', Arial, sans-serif !important;
            text-align: right;
        }
        
        .page-header {
            text-align: center;
        }
        
        .query-info, .timestamp {
            text-align: right;
        }
        
        /* Ensure proper text flow for mixed content */
        p, div, span {
            direction: rtl;
            text-align: right;
        }
        
        /* Handle code blocks and pre-formatted text */
        pre, code {
            direction: ltr;
            text-align: left;
        }
        
        /* Lists should align properly */
        ul, ol {
            text-align: right;
            padding-right: 20px;
            padding-left: 0;
        }
        
        /* Headers maintain center alignment but support RTL text */
        h1, h2, h3, h4, h5, h6 {
            direction: rtl;
            text-align: right;
        }
        
        /* Footer center aligned */
        .page-footer {
            text-align: center;
        }
        """
    
    # Build complete HTML document
    html_doc = f"""<!DOCTYPE html>
<html lang="{language}" dir="{direction}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SocioGraph Answer - {query[:50]}...</title>
    <meta name="generator" content="SocioGraph">
    <meta name="created" content="{timestamp}">
    <style>
        {css_content if css_content else _get_default_css()}
        
        {rtl_css}
        
        /* Print-specific styles */
        @media print {{
            body {{
                margin: 0;
                padding: 2cm;
                font-size: 12pt;
                line-height: 1.5;
            }}
            
            .page-header {{
                margin-bottom: 30px;
                text-align: center;
            }}
            
            .page-footer {{
                margin-top: 50px;
                text-align: center;
                font-size: 10pt;
                color: #666;
                border-top: 1px solid #ddd;
                padding-top: 20px;
            }}
            
            /* Better page breaks */
            h1, h2, h3 {{
                page-break-after: avoid;
            }}
            
            p {{
                orphans: 3;
                widows: 3;
            }}
        }}
        
        /* Page settings for PDF */
        @page {{
            size: A4;
            margin: 2cm;
        }}
    </style>
</head>
<body>
    <div class="page-header">
        <h1>SocioGraph Answer</h1>
        <div class="query-info">
            <strong>Query:</strong> {query}
        </div>
        <div class="timestamp">
            <strong>Generated:</strong> {timestamp}
        </div>
    </div>
    
    <main>
        {html_body}
    </main>
    
    <div class="page-footer">
        <p><em>Generated by SocioGraph - AI-powered document analysis and knowledge graph</em></p>
    </div>
</body>
</html>"""

    return html_doc


def _get_default_css() -> str:
    """Get default CSS styling for PDF."""
    return """
        body {
            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        
        h1, h2, h3 {
            color: #0066cc;
            margin-top: 1.5em;
        }
        
        h1 {
            text-align: center;
            border-bottom: 2px solid #0066cc;
            padding-bottom: 10px;
        }
        
        a {
            color: #0066cc;
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
        
        code {
            background-color: #f5f5f5;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        
        pre {
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
        }
        
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        
        blockquote {
            border-left: 4px solid #0066cc;
            margin-left: 0;
            padding-left: 20px;
            color: #666;
        }
        
        .entity {
            color: #0066cc;
            font-weight: bold;
        }
        
        .relation {
            color: #009900;
            font-style: italic;
        }
    """


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
    # This helps Playwright locate images properly
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


async def save_pdf_async(answer_md: str, query: str, filename: Optional[str] = None, language: str = "en") -> Path:
    """Async version of PDF generation using Playwright."""
    _logger.info(f"Starting async PDF generation for query: {query[:100]}... (language: {language})")
    
    await _initialize_playwright()
    
    if not _playwright_available:
        _logger.warning("Playwright not available - falling back to HTML")
        return _save_as_html(answer_md, query, filename, language)
    
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
        
        # Build HTML document with language support
        html_content = _build_html_document(answer_md, query, language)
        
        # Process any embedded resources
        html_content = _process_embedded_resources(html_content)
        
        # Get browser and create new context
        browser = await get_browser()
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Set content and wait for it to load
            await page.set_content(html_content, wait_until="networkidle")
              # Emulate print media for proper styling
            await page.emulate_media(media="print")
              # Generate PDF with optimized settings
            _logger.info(f"Rendering PDF to {output_path}")
            await page.pdf(
                path=str(output_path),
                format="A4",
                margin={"top": "15mm", "bottom": "15mm", "left": "15mm", "right": "15mm"},
                print_background=True
                # Note: generate_tagged_pdf and generate_document_outline are not supported in Playwright
            )
            
        finally:
            # Always close the context to free memory
            await context.close()
        
        # Verify file was created
        if output_path.exists():
            file_size = output_path.stat().st_size
            _logger.info(f"PDF successfully created: {output_path} ({file_size} bytes)")
            
            # Clean up old files to maintain the saved files limit
            try:
                removed_count = cleanup_old_saved_files()
                if removed_count > 0:
                    _logger.info(f"Cleaned up {removed_count} old saved files to maintain limit of {_cfg.SAVED_LIMIT}")
            except Exception as cleanup_error:
                _logger.warning(f"Failed to clean up old saved files: {cleanup_error}")
            
            return output_path
        else:
            raise RuntimeError("PDF file was not created")
            
    except Exception as e:
        _logger.error(f"Error generating PDF: {e}")
        _logger.info("Falling back to HTML format...")
        return _save_as_html(answer_md, query, filename, language)


def save_pdf(answer_md: str, query: str, filename: Optional[str] = None, language: str = "en") -> Path:
    """Synchronous wrapper for PDF generation."""
    _logger.info(f"Starting PDF generation for query: {query[:100]}... (language: {language})")
    
    # Check if we're in an async context
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context, schedule the async version
        return asyncio.run_coroutine_threadsafe(
            save_pdf_async(answer_md, query, filename, language), 
            loop
        ).result(timeout=30)
    except RuntimeError:
        # No async loop, use sync implementation
        return _save_pdf_sync(answer_md, query, filename, language)


def _save_pdf_sync(answer_md: str, query: str, filename: Optional[str] = None, language: str = "en") -> Path:
    """Synchronous PDF generation using Playwright."""
    _initialize_sync_playwright()
    
    if not _sync_browser:
        _logger.warning("Sync Playwright not available - falling back to HTML")
        return _save_as_html(answer_md, query, filename, language)
    
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
        
        # Build HTML document with language support
        html_content = _build_html_document(answer_md, query, language)
        
        # Process any embedded resources
        html_content = _process_embedded_resources(html_content)
        
        # Create new context and page
        context = _sync_browser.new_context()
        page = context.new_page()
        
        try:
            # Set content and wait for it to load
            page.set_content(html_content, wait_until="networkidle")
              # Emulate print media for proper styling
            page.emulate_media(media="print")
            
            # Generate PDF
            _logger.info(f"Rendering PDF to {output_path}")
            page.pdf(
                path=str(output_path),
                format="A4",
                margin={"top": "15mm", "bottom": "15mm", "left": "15mm", "right": "15mm"},
                print_background=True
                # Note: generate_tagged_pdf and generate_document_outline are not supported in Playwright
            )
            
        finally:
            # Always close the context to free memory
            context.close()
          # Verify file was created
        if output_path.exists():
            file_size = output_path.stat().st_size
            _logger.info(f"PDF successfully created: {output_path} ({file_size} bytes)")
            
            # Clean up old files to maintain the saved files limit
            try:
                removed_count = cleanup_old_saved_files()
                if removed_count > 0:
                    _logger.info(f"Cleaned up {removed_count} old saved files to maintain limit of {_cfg.SAVED_LIMIT}")
            except Exception as cleanup_error:
                _logger.warning(f"Failed to clean up old saved files: {cleanup_error}")
            
            return output_path
        else:
            raise RuntimeError("PDF file was not created")
            
    except Exception as e:
        _logger.error(f"Error generating PDF: {e}")
        _logger.info("Falling back to HTML format...")
        return _save_as_html(answer_md, query, filename, language)


def _save_as_html(answer_md: str, query: str, filename: Optional[str] = None, language: str = "en") -> Path:
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
      # Build HTML document with language support
    html_content = _build_html_document(answer_md, query, language)
    
    # Write HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    _logger.info(f"HTML file created: {output_path}")
    return output_path


def check_playwright_environment() -> Dict[str, Any]:
    """Check the environment for Playwright configuration."""
    env_info = {
        "playwright_available": _playwright_available,
        "playwright_initialized": _playwright_initialized,
        "browser_connected": _browser.is_connected() if _browser else False,
        "sync_browser_connected": _sync_browser.is_connected() if _sync_browser else False,
    }
    
    if _playwright_available:
        try:
            import pkg_resources
            env_info["playwright_version"] = pkg_resources.get_distribution("playwright").version
        except (ImportError, pkg_resources.DistributionNotFound):
            env_info["playwright_version"] = "Not available"
    
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


async def cleanup_resources():
    """Clean up Playwright resources."""
    global _browser, _sync_browser
    
    if _browser:
        await _browser.close()
        _browser = None
    
    if _sync_browser:
        _sync_browser.close()
        _sync_browser = None
    
    _logger.info("Playwright resources cleaned up")


# Legacy compatibility functions for existing code
def WEASYPRINT_AVAILABLE() -> bool:
    """Legacy compatibility function - now checks Playwright availability."""
    return is_playwright_available()


def check_weasyprint_environment() -> Dict[str, Any]:
    """Legacy compatibility function - now returns Playwright environment info."""
    return check_playwright_environment()
