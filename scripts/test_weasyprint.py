"""
Test script to verify WeasyPrint PDF generation works correctly.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path to allow importing from the backend
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backend.app.answer.pdf import save_pdf, WEASYPRINT_AVAILABLE, FONT_CONFIG_AVAILABLE

def test_pdf_generation():
    """Test PDF generation with WeasyPrint."""
    print(f"WeasyPrint available: {WEASYPRINT_AVAILABLE}")
    print(f"FontConfiguration available: {FONT_CONFIG_AVAILABLE}")
    
    # Create a simple markdown test document
    test_markdown = """
# Test PDF Generation

This is a test document to verify that WeasyPrint is working correctly.

## Features to test

1. **Bold text** and *italic text*
2. [Links](https://example.com)
3. Code blocks:

```python
def hello_world():
    print("Hello, World!")
```

4. Tables:

| Name | Value |
|------|-------|
| Test 1 | 100 |
| Test 2 | 200 |

"""
    
    try:
        # Generate PDF
        output_path = save_pdf(test_markdown, "Test PDF Generation", "test_weasyprint")
        print(f"PDF generated successfully: {output_path}")
        print(f"File size: {output_path.stat().st_size} bytes")
        return True
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return False

if __name__ == "__main__":
    success = test_pdf_generation()
    sys.exit(0 if success else 1)
