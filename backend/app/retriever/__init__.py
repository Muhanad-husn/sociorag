"""SocioGraph retrieval module.

This module provides the main retrieval pipeline for the SocioGraph system.
It handles language detection, vector retrieval, graph retrieval, and context
merging for answering user queries.
"""

from backend.app.retriever.pipeline import retrieve_context

# Export the main entry point
__all__ = ["retrieve_context"]