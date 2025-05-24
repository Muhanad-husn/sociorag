# **SocioGraph Rebuild — Phase 6 Deep‑Dive Plan**

> **Objective:** Wire together all backend pieces into a **FastAPI** server that exposes REST and Server‑Sent‑Events endpoints for ingestion, querying, history, and asset download.

---

## 🎯 Outcomes

| ID | Outcome | Acceptance Criteria |
|----|---------|---------------------|
| O‑6.1 | All routes described in Phase 6 spec respond with **2xx** when called with valid payloads. | `pytest backend/tests/test_api.py::test_routes_ok` passes. fileciteturn5file2 |
| O‑6.2 | `/search` streams answer tokens as **SSE** with < 1 s initial latency. | Front‑end displays live typing. |
| O‑6.3 | `/upload` triggers Phase 3 ingest **asynchronously** and returns JSON `{status:"uploaded"}` immediately. | Upload test checks non‑blocking. |
| O‑6.4 | `/reset` clears vector store, DB, input & saved dirs, and history file. | Directory listing is empty after call. |
| O‑6.5 | PDFs saved by Phase 5 are downloadable via `/saved/{id}` and served with `Content‑Disposition: attachment`. | `curl -OJ` retrieves file. |
| O‑6.6 | API **docs** available at `/docs` and reflect every route. | Swagger UI lists 6 endpoints. |
| O‑6.7 | Uvicorn server starts with `uvicorn backend.app.main:app --reload` and hot‑reloads code. | Manual check. |

---

## 📋 Route Matrix fileciteturn5file2

| Method & Path | Purpose | Payload / Query | Response |
|---------------|---------|-----------------|----------|
| `POST /upload` | Upload a PDF and queue ingestion | `multipart/form-data` field `file` | `{status:"uploaded",file:"foo.pdf"}` |
| `POST /process` | Manually trigger `process_all()` | none | `{status:"processing"}` |
| `POST /search` | Stream bilingual answer tokens | `{query:"…",temperature?,top_k?,top_k_r?}` | **SSE** `event:token` |
| `POST /reset` | Full reset of corpus & history | none | `{status:"corpus cleared"}` |
| `GET /history` | List last 15 queries | none | JSONL array → list[obj] |
| `GET /saved/{id}` | Download stored PDF | path `id` like `20250525T120012Z.pdf` | `application/pdf` |

---

## ⚙️ Prerequisites

* **Phases 0‑5 complete** (ingest, retrieval, answer generation working).
* Packages already installed earlier: `fastapi`, `uvicorn[standard]`, `sse-starlette`.
* Development auto‑reload:

```bash
pip install python-multipart watchdog
```

---

## 🛠️ Step‑by‑Step Implementation

### 1  Create **`backend/app/main.py`**

```python
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.app.core import LoggerSingleton, get_config
from backend.app.api import ingest, qa

cfg = get_config()
LoggerSingleton().info("Starting SocioGraph API")

app = FastAPI(
    title="SocioGraph API",
    version="0.6.0",
    description="HybridRAG backend exposing ingestion & search endpoints.",
)

# CORS for local Preact dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(ingest.router, prefix="")
app.include_router(qa.router, prefix="")

# Static: serve saved PDFs
saved_dir = Path(cfg.SAVED_DIR)
saved_dir.mkdir(exist_ok=True)
app.mount("/saved", StaticFiles(directory=saved_dir), name="saved")
```

### 2  Refactor Routers

* **`backend/app/api/ingest.py`**
  * Already partially built in Phase 3; add `/process` route that simply calls `process_all()` in a background task.
* **`backend/app/api/qa.py`**
  * Built in Phase 5; ensure tri‑lingual JSON body validation with Pydantic model:

  ```python
  from pydantic import BaseModel

  class SearchPayload(BaseModel):
      query: str
      temperature: float | None = None
      top_k: int | None = None
      top_k_r: int | None = None
  ```

*Return SSE stream using **sse‑starlette**.*

### 3  History Endpoint (`history.py`)

```python
from fastapi import APIRouter, HTTPException
import json, itertools
from backend.app.answer.history import _hist

router = APIRouter()

@router.get("/history")
def get_history(limit: int = 15):
    if not _hist.exists():
        return []
    with open(_hist, encoding="utf-8") as f:
        lines = list(itertools.islice(reversed(f.readlines()), limit))
    return [json.loads(l) for l in lines]
```

Register `history.router` in `main.py`.

### 4  Reset Route Implementation

Reuse `reset_corpus()` from Phase 3:

```python
@router.post("/reset")
def reset():
    reset_corpus()
    return {"status": "corpus cleared"}
```

### 5  Run Script

Add **`backend/__main__.py`**:

```python
import uvicorn
from backend.app.main import app

uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
```

Enables `python -m backend`.

### 6  Unit & Integration Tests (`test_api.py`)

```python
import pytest, asyncio, httpx, os, io, pathlib, json
from fastapi import status
from backend.app.main import app

@pytest.mark.asyncio
async def test_routes_ok(tmp_path):
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        # upload
        pdf_bytes = b"%PDF-1.4 test"
        resp = await client.post("/upload", files={"file": ("doc.pdf", pdf_bytes, "application/pdf")})
        assert resp.status_code == status.HTTP_200_OK
        # search (non‑stream)
        resp = await client.post("/search", json={"query": "Hello"})
        assert resp.status_code == status.HTTP_200_OK
        # reset
        resp = await client.post("/reset")
        assert resp.json()["status"] == "corpus cleared"
```

---

## 📝 Validation Checklist

1. `uvicorn backend.app.main:app --reload` opens at `http://127.0.0.1:8000/docs`.
2. Upload sample PDF → check logs show background ingest.
3. Execute search in Swagger → browser SSE shows streaming.
4. Download generated PDF from `/saved/<id>.pdf`.
5. Inspect `/history` endpoint returns latest query.

---

## 🕑 Estimated Effort

| Task | Time (min) |
|------|------------|
| Main app & CORS | 5 |
| Router wiring & payload validation | 10 |
| SSE + streaming logic | 10 |
| Static files & download | 5 |
| Tests & docs | 10 |
| **Total** | **~40 min** |

---

## 🚑 Troubleshooting & Tips

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| **SSE stops after 30 s** | Browser keep‑alive timeout | Add heartbeat: `yield ":"` every 15 s |
| **PDF 404** | Saved path difference | Ensure `cfg.SAVED_DIR` matches mount path |
| **CORS errors** | Origin mismatch | Update `allow_origins` list in `main.py` |
| **Auto‑reload slow** | `watchgod` scanning large dirs | Exclude `vector_store/` via `--reload-dir` |

---

## 📝 Deliverables

1. **`backend/app/main.py`** (FastAPI app).  
2. Updated routers: `ingest.py`, `qa.py`, `history.py`.  
3. **`backend/__main__.py`** entrypoint.  
4. Tests under `backend/tests/test_api.py`.  
5. Launch instructions in README.  
6. Git tag **`phase‑6`**.

---

_When the server boots, endpoints respond per the Route Matrix, and Swagger UI lists all routes, **Phase 6 is complete**. Next: **Phase 7 – Preact / Tailwind Front‑End**._
