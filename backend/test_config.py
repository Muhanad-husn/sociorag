"""Test script to validate the configuration system."""

import os
import importlib
from pathlib import Path

# Add the parent directory to sys.path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the configuration module
from app.core.config import get_config

def test_config():
    """Test the configuration system."""
    # Test default config
    cfg = get_config()
    print("Default config:")
    print(f"ENTITY_SIM = {cfg.ENTITY_SIM}")
    assert cfg.ENTITY_SIM == 0.90, f"Expected ENTITY_SIM to be 0.90, got {cfg.ENTITY_SIM}"
    print("✅ Defaults OK")

    # Test .env override
    os.environ["ENTITY_SIM"] = "0.88"
    importlib.reload(sys.modules["backend.app.core.config"])
    from app.core.config import get_config as get_config_reloaded
    cfg2 = get_config_reloaded()
    print("\n.env override:")
    print(f"ENTITY_SIM = {cfg2.ENTITY_SIM}")
    assert cfg2.ENTITY_SIM == 0.88, f"Expected ENTITY_SIM to be 0.88, got {cfg2.ENTITY_SIM}"
    print("✅ .env override works")    # Test YAML override
    yaml_path = Path("config.yaml")
    importlib.reload(sys.modules["backend.app.core.config"])
    from app.core.config import get_config as get_config_reloaded2
    cfg3 = get_config_reloaded2(yaml_path)
    print("\nYAML override:")
    print(f"TOP_K = {cfg3.TOP_K}")
    assert cfg3.TOP_K == 50, f"Expected TOP_K to be 50, got {cfg3.TOP_K}"
    print("✅ YAML override works")

if __name__ == "__main__":
    test_config()
