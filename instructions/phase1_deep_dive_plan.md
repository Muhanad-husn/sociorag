# **SocioGraph Rebuild — Phase 1 Deep‑Dive Plan**

> **Objective:** Centralise every project‑wide tunable in an importable, override‑friendly `Config` singleton (Python) so that later phases can change behaviour by editing **one file** instead of digging through the codebase.

---

## 🎯 Outcomes

| ID | Outcome | Acceptance Criteria |
|----|---------|---------------------|
| O‑1.1 | `backend/app/core/config.py` contains a `get_config()` function that returns a cached singleton. | `from core.config import get_config; get_config() is get_config()` |
| O‑1.2 | All defaults listed below are represented as typed attributes. | `dir(cfg)` shows every field |
| O‑1.3 | **`.env`** values automatically override defaults. | `CHUNK_SIM` changes when `.env` sets it |
| O‑1.4 | **`config.yaml`** overrides are supported (explicit arg). | `get_config(Path("config.yaml")).TOP_K == 50` |
| O‑1.5 | README section **“Global Configuration”** documents every field and shows override examples. | Reviewer signs off |

---

## 📋 Default Configuration Matrix

| Group | Field | Default | Rationale |
|-------|-------|---------|-----------|
| **Paths** | `BASE_DIR` | repo root | anchor for other dirs |
|  | `INPUT_DIR` | `BASE_DIR/input` | raw PDFs |
|  | `SAVED_DIR` | `BASE_DIR/saved` | generated PDFs |
|  | `VECTOR_DIR` | `BASE_DIR/vector_store` | ChromaDB fileciteturn1file1 |
|  | `GRAPH_DB` | `BASE_DIR/graph.db` | SQLite + VSS store |
|  | `PDF_THEME` | `BASE_DIR/resources/pdf_theme.css` | branding |
| **Models** | `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` |
|  | `RERANKER_MODEL` | `cross-encoder/ms-marco-MiniLM-L6-v2` fileciteturn1file13 |
|  | `ENTITY_LLM_MODEL` | `google/gemini-flash-1.5` |
|  | `ANSWER_LLM_MODEL` | `meta-llama/llama-3.3-70b-instruct:free` |
|  | `TRANSLATE_LLM_MODEL` | `mistralai/mistral-nemo:free` |
| **Thresholds / params** | `CHUNK_SIM` | **0.85** fileciteturn1file1 |
|  | `ENTITY_SIM` | **0.90** fileciteturn1file1 |
|  | `GRAPH_SIM` | **0.95** fileciteturn1file5 |
|  | `TOP_K` | `100` |
|  | `TOP_K_RERANK` | `15` |
|  | `MAX_CONTEXT_FRACTION` | `0.4` |
| **Resources** | `SPACY_MODEL` | `en_core_web_sm` |
|  | `LOG_LEVEL` | `INFO` |
| **Limits** | `HISTORY_LIMIT` | 15 |
|  | `SAVED_LIMIT` | 15 |

---

## ⚙️ Prerequisites

* **Phase 0 completed** (env active, repo scaffold).  
* Extra packages:

```bash
pip install pydantic>=2 python-dotenv pyyaml
```

* `.env` file **NOT** committed; store `OPENROUTER_API_KEY` here per the OpenRouter guide fileciteturn1file6.

---

## 🛠️ Implementation Steps

### 1  Create `backend/app/core/config.py`

```python
"""Central configuration singleton for SocioGraph."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

class _Config(BaseSettings):
    # ---------------------- paths ---------------------- #
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    INPUT_DIR: Path = BASE_DIR / "input"
    SAVED_DIR: Path = BASE_DIR / "saved"
    VECTOR_DIR: Path = BASE_DIR / "vector_store"
    GRAPH_DB: Path = BASE_DIR / "graph.db"
    PDF_THEME: Path = BASE_DIR / "resources" / "pdf_theme.css"

    # ---------------------- models --------------------- #
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L6-v2"
    ENTITY_LLM_MODEL: str = "google/gemini-flash-1.5"
    ANSWER_LLM_MODEL: str = "meta-llama/llama-3.3-70b-instruct:free"
    TRANSLATE_LLM_MODEL: str = "mistralai/mistral-nemo:free"

    # ---------------- thresholds & params -------------- #
    CHUNK_SIM: float = 0.85
    ENTITY_SIM: float = 0.90
    GRAPH_SIM: float = 0.95
    TOP_K: int = 100
    TOP_K_RERANK: int = 15
    MAX_CONTEXT_FRACTION: float = 0.4

    # ---------------- resources & misc ---------------- #
    SPACY_MODEL: str = "en_core_web_sm"
    LOG_LEVEL: str = "INFO"
    HISTORY_LIMIT: int = 15
    SAVED_LIMIT: int = 15

    # pydantic‑settings behaviour
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf‑8",
        extra="ignore",      # ignore unknown keys
        frozen=True          # make immutable
    )

def _apply_yaml_overrides(cfg: _Config, yaml_path: Optional[Path]) -> _Config:
    """Return a *new* Config overridden by YAML if provided."""
    if yaml_path and Path(yaml_path).exists():
        data = yaml.safe_load(Path(yaml_path).read_text()) or {}
        return cfg.model_copy(update=data)
    return cfg

@lru_cache
def get_config(yaml_path: Optional[Path] = None) -> _Config:
    """Return **singleton** Config; optional YAML path applied on first call."""
    return _apply_yaml_overrides(_Config(), yaml_path)
```

### 2  Add Override Artefacts

```bash
# .env.example (do not commit real keys)
OPENROUTER_API_KEY=sk-...
CHUNK_SIM=0.80
LOG_LEVEL=DEBUG
```

```yaml
# config.yaml.example
chunk_sim: 0.8
top_k: 50
vector_dir: /mnt/fast_ssd/vector_store
```

### 3  Update `README.md`

Add a **Global Configuration** section:

```
### Changing Defaults

1. Copy `.env.example` → `.env` and tweak numeric thresholds.
2. Or create `config.yaml` and pass its path to `get_config()`:

```python
from backend.app.core.config import get_config
cfg = get_config("config.yaml")
print(cfg.TOP_K)   # 50
```
```

### 4  Quick Validation

```bash
python - <<'PY'
from backend.app.core.config import get_config
cfg = get_config()
assert cfg.ENTITY_SIM == 0.90
print("✅ Defaults OK")

# `.env` override demo
import os, importlib
os.environ["ENTITY_SIM"] = "0.88"
importlib.reload(get_config.__wrapped__)  # drop cache
cfg2 = get_config()
assert cfg2.ENTITY_SIM == 0.88
print("✅ .env override works")
PY
```

---

## 🕑 Estimated Effort

| Task | Time (min) |
|------|------------|
| Add packages & imports | 3 |
| Implement `config.py` | 10 |
| Create examples & README docs | 5 |
| Validation | 2 |
| **Total** | **~20 min** |

---

## 🚑 Troubleshooting & Tips

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `AttributeError: model_copy` | pydantic < 2.0 | `pip install --upgrade pydantic` |
| `.env` values ignored | Wrong cwd when running script | Chdir to repo root or set `env_file` absolute path |
| YAML overrides not applied | Forgot to pass path to `get_config()` | `get_config("config.yaml")` |

---

## 📝 Deliverables

1. `backend/app/core/config.py`
2. `.env.example` + `config.yaml.example`
3. Updated README section
4. Git tag `phase‑1`

Once all acceptance tests pass, proceed to **Phase 2 – Infrastructure Singletons**.

