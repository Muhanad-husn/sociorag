"""Reset helper for SocioGraph.

This module provides functions to reset the corpus state by clearing the vector store,
input directory, saved directory, and graph database.
"""

import shutil
from pathlib import Path

from backend.app.core.config import get_config


def reset_corpus():
    """Reset the corpus by clearing all data stores.
    
    This function:
    1. Removes and recreates the vector store directory
    2. Removes and recreates the input directory
    3. Removes and recreates the saved directory
    4. Deletes the graph database file
    """
    cfg = get_config()
    
    # Clear directories
    for path in [cfg.VECTOR_DIR, cfg.INPUT_DIR, cfg.SAVED_DIR]:
        shutil.rmtree(path, ignore_errors=True)
        path.mkdir(exist_ok=True)
    
    # Delete graph database
    Path(cfg.GRAPH_DB).unlink(missing_ok=True)
    
    return {"status": "corpus cleared"}