"""Central configuration singleton for SocioGraph."""

from functools import lru_cache
from pathlib import Path
from typing import Optional, Annotated

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class _Config(BaseSettings):
    # ---------------------- paths ---------------------- #
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    INPUT_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent.parent / "input")
    SAVED_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent.parent / "saved")
    VECTOR_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent.parent / "vector_store")
    GRAPH_DB: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent.parent / "data" / "graph.db")
    PDF_THEME: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent.parent / "resources" / "pdf_theme.css")

    # ---------------------- models --------------------- #
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"  # Fixed model name with hyphen in L-6
    ENTITY_LLM_MODEL: str = "google/gemini-flash-1.5"
    ANSWER_LLM_MODEL: str = "meta-llama/llama-3.3-70b-instruct:free"
    TRANSLATE_LLM_MODEL: str = "mistralai/mistral-nemo:free"    # ---------------- thresholds & params -------------- #
    CHUNK_SIM: float = 0.85
    ENTITY_SIM: float = 0.90
    GRAPH_SIM: float = 0.95
    TOP_K: int = 100
    TOP_K_RERANK: int = 15
    MAX_CONTEXT_FRACTION: float = 0.4

    # ---------------------- API keys ------------------- #
    OPENROUTER_API_KEY: Optional[str] = None

    # ---------------- resources & misc ---------------- #
    SPACY_MODEL: str = "en_core_web_sm"
    LOG_LEVEL: str = "INFO"
    HISTORY_LIMIT: int = 15
    SAVED_LIMIT: int = 15

    # pydantic-settings behavior
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",      # ignore unknown keys
        frozen=True          # make immutable
    )

def _apply_yaml_overrides(cfg: _Config, yaml_path: Optional[Path]) -> _Config:
    """Return a *new* Config overridden by YAML if provided."""
    if yaml_path and Path(yaml_path).exists():
        try:
            data = yaml.safe_load(Path(yaml_path).read_text()) or {}
            # Create a new config with the overrides
            update_data = {}
            for key, value in data.items():
                update_data[key.upper()] = value
            return cfg.model_copy(update=update_data)
        except Exception as e:
            print(f"Error loading YAML file: {e}")
    return cfg

@lru_cache
def get_config(yaml_path: Optional[Path] = None) -> _Config:
    """Return **singleton** Config; optional YAML path applied on first call."""
    return _apply_yaml_overrides(_Config(), yaml_path)
