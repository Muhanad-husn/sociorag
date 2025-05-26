"""Test Phase 5 implementation - Answer generation and PDF export.

This script tests the answer generation pipeline to ensure it works correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.app.answer.generator import generate_answer_complete
from backend.app.answer.pdf import save_pdf
from backend.app.answer.history import append_record
from backend.app.core.singletons import LoggerSingleton
from backend.app.core.config import get_config

_logger = LoggerSingleton().get()
_cfg = get_config()


async def test_answer_generation():
    """Test the answer generation pipeline."""
    print("Testing Phase 5 - Answer Generation & PDF Export")
    print("=" * 50)
    
    # Test query and mock context
    test_query = "What is a knowledge graph?"
    test_context = [
        "A knowledge graph is a network of real-world entities and their relationships.",
        "Knowledge graphs represent information in a structured format using nodes and edges.",
        "They are used in AI systems to store and query interconnected data."
    ]
    
    try:
        print(f"Query: {test_query}")
        print(f"Context items: {len(test_context)}")
        
        # Test answer generation
        print("\n1. Generating answer...")
        answer = await generate_answer_complete(test_query, test_context)
        print(f"Answer generated: {len(answer)} characters")
        print(f"Answer preview: {answer[:200]}...")
        
        # Test PDF generation
        print("\n2. Generating PDF...")
        pdf_path = save_pdf(answer, test_query)
        print(f"PDF saved to: {pdf_path}")
        print(f"PDF file exists: {pdf_path.exists()}")
        print(f"PDF file size: {pdf_path.stat().st_size} bytes")
        
        # Test history logging
        print("\n3. Logging to history...")
        append_record(
            query=test_query,
            pdf_path=pdf_path,
            token_count=len(answer.split()),
            context_count=len(test_context),
            duration=1.5,
            metadata={"test": True}
        )
        print("History record added successfully")
        
        print("\n✅ Phase 5 test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        _logger.error(f"Phase 5 test failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_answer_generation())
    sys.exit(0 if success else 1)
