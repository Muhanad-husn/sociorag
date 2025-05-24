"""Unit tests for the configuration module."""
import os
import importlib
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

def test_config_defaults():
    """Test that the default configuration values are correct."""
    from backend.app.core.config import get_config
    
    cfg = get_config()
    assert cfg.CHUNK_SIM == 0.85
    assert cfg.ENTITY_SIM == 0.90
    assert cfg.GRAPH_SIM == 0.95
    assert cfg.TOP_K == 100
    assert cfg.TOP_K_RERANK == 15
    assert cfg.MAX_CONTEXT_FRACTION == 0.4
    assert cfg.SPACY_MODEL == "en_core_web_sm"
    assert cfg.LOG_LEVEL == "INFO"
    assert cfg.HISTORY_LIMIT == 15
    assert cfg.SAVED_LIMIT == 15

def test_env_override():
    """Test that environment variables override default values."""
    # Set environment variables
    os.environ["CHUNK_SIM"] = "0.75"
    os.environ["TOP_K"] = "50"
    
    # Reload the module to clear the lru_cache
    if "backend.app.core.config" in sys.modules:
        importlib.reload(sys.modules["backend.app.core.config"])
    
    # Import and test
    from backend.app.core.config import get_config
    cfg = get_config()
    assert cfg.CHUNK_SIM == 0.75
    assert cfg.TOP_K == 50

def test_yaml_override():
    """Test that YAML configuration overrides default values."""
    # Create a temporary YAML file
    yaml_path = Path("test_config.yaml")
    yaml_path.write_text("""
    chunk_sim: 0.80
    top_k: 25
    entity_sim: 0.95
    """)
    
    try:
        # Reload the module to clear the lru_cache
        if "backend.app.core.config" in sys.modules:
            importlib.reload(sys.modules["backend.app.core.config"])
        
        # Import and test
        from backend.app.core.config import get_config
        cfg = get_config(yaml_path)
        assert cfg.CHUNK_SIM == 0.80
        assert cfg.TOP_K == 25
        assert cfg.ENTITY_SIM == 0.95
    finally:
        # Clean up
        yaml_path.unlink(missing_ok=True)

if __name__ == "__main__":
    # Run the tests
    test_config_defaults()
    print("✅ Default configuration test passed")
    
    test_env_override()
    print("✅ Environment variable override test passed")
    
    test_yaml_override()
    print("✅ YAML configuration override test passed")
    
    print("\nAll tests passed! 🎉")
