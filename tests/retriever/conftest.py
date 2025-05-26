"""
Configuration for pytest in the retriever tests directory.
Helps with module import paths and test discovery.
"""

import sys
import os
import pytest
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

# Import necessary modules with project root in path
from backend.app.core.singletons import get_logger
from backend.app.retriever.vector import retrieve_chunks

@pytest.fixture
def chunks():
    """Fixture to provide chunks for reranking tests."""
    # This will run the vector retrieval to get chunks for tests that need them
    query_text = "What are the impacts of climate change on biodiversity?"
    chunks = retrieve_chunks(query_text=query_text)
    return chunks
