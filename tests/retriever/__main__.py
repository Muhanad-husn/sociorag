# filepath: d:\sociorag\tests\retriever\__main__.py
"""
Main entry point for running retriever tests as a module.
Example: python -m tests.retriever
"""

import sys
import os
import unittest
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

if __name__ == "__main__":
    import pytest
    # Run all tests in this directory
    pytest.main(["-v", str(Path(__file__).parent)])
