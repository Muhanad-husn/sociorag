# **SocioGraph Rebuild — Phase 3 Deep‑Dive Plan**

> **Objective:** Transform uploaded PDFs into **semantic chunks**, embed them into the Chroma vector store, and populate the SQLite knowledge‑graph with deduplicated entities and relationships. This phase provides the fuel that every later query relies on.

---

## 🎯 Outcomes

| ID | Outcome | Acceptance Criteria |
|----|---------|---------------------|
| O‑3.1 | **Reset** endpoint completely clears state. | After `POST /reset` the folders `vector_store/`, `input/`, `saved/`, and file `graph.db` no longer exist. |
| O‑3.2 | **Upload** endpoint stores PDFs in `input/` with original filenames (minus extension). | Uploading `doc.pdf` results in `input/doc.pdf`. |
| O‑3.3 | `ingest.process_all()` converts every page into semantic chunks (≈ 1‑3 paragraphs each). | Average chunk length 40–120 tokens; no chunk crosses section boundaries. |
| O‑3.4 | All chunks embedded and persisted to Chroma collection `chunks`. | `collection.count()` equals total chunks after ingest. |
| O‑3.5 | Entities & relations extracted and written to `graph.db`, reusing existing IDs when cosine ≥ 0.90. | No duplicate entity rows for surface strings that differ only in whitespace/case. |
| O‑3.6 | End‑to‑end processing of a 5‑page PDF completes in **< 30 s** on a CPU laptop. | Timer test passes. |
| O‑3.7 | Progress stream sends JSON updates (`phase`, `percent`) to the client. | UI displays real‑time progress bar. |

---

## 📋 Pipeline Overview fileciteturn3file0

```
PDF → text pages
      ↓
SemanticSplitterNodeParser
      ↓
       chunks ──► Sentence‑Transformer Embedding ──► Chroma ('chunks')
      ↓
LLM Entity/Relation JSON (graph_prompts.py)
      ↓
Dedup via sqlite‑vss ANN (sim ≥ 0.90)
      ↓
SQLite tables: entity, relation
```

---

## ⚙️ Prerequisites

* **Phases 0‑2 complete** (env + Config + singletons).  
* Extra packages:

```bash
pip install pypdf llama-index pdfminer.six
```

* `OPENROUTER_API_KEY` exported.

---

## 🛠️ Step‑by‑Step Implementation

### 1  Endpoints Skeleton (`backend/app/api/ingest.py`)

```python
from fastapi import APIRouter, UploadFile, BackgroundTasks
from backend.app.ingest.pipeline import process_all, reset_corpus

router = APIRouter(tags=["ingest"])

@router.post("/reset")
async def reset():
    reset_corpus()
    return {"status": "corpus cleared"}

@router.post("/upload")
async def upload(file: UploadFile, tasks: BackgroundTasks):
    dest = (get_config().INPUT_DIR / file.filename).with_suffix(".pdf")
    dest.write_bytes(await file.read())
    tasks.add_task(process_all)   # run async
    return {"status": "uploaded", "file": dest.name}
```

### 2  Reset Helper (`backend/app/ingest/reset.py`)

```python
def reset_corpus():
    cfg = get_config()
    for path in [cfg.VECTOR_DIR, cfg.INPUT_DIR, cfg.SAVED_DIR]:
        shutil.rmtree(path, ignore_errors=True)
        path.mkdir(exist_ok=True)
    Path(cfg.GRAPH_DB).unlink(missing_ok=True)
```

### 3  PDF Loader (`backend/app/ingest/loader.py`)

Use **pypdf** to extract page text:

```python
from pypdf import PdfReader
def load_pages(pdf_path: Path) -> list[str]:
    reader = PdfReader(pdf_path)
    return [p.extract_text() or "" for p in reader.pages]
```

### 4  Semantic Chunking fileciteturn3file6

```python
from llama_index.node_parser import SemanticSplitterNodeParser
from backend.app.core import embed

_SPLITTER = SemanticSplitterNodeParser(
    buffer_size=2,                          # per guideline
    breakpoint_percentile_threshold=60,     # aggressive for PDFs
    embed_model=None,                       # we supply pre‑embedded text
)

def chunk_page(text: str) -> list[str]:
    nodes = _SPLITTER.split_text(text)
    return [n.get_content().strip() for n in nodes if n.get_content().strip()]
```

*Average chunk target ≈ 80 tokens (tuned via `breakpoint_percentile_threshold`).*

### 5  Vector Index

```python
from backend.app.core import ChromaSingleton, embed

def add_chunks(chunks: list[str], source_file: str):
    vecs = embed(chunks)
    ids  = [f"{source_file}:{i}" for i in range(len(chunks))]
    meta = [{"text": c, "file": source_file} for c in chunks]
    ChromaSingleton().add_texts(chunks, embeddings=vecs, metadatas=meta, ids=ids)
```

### 6  Entity & Relation Extraction fileciteturn3file8

```python
import json, asyncio
from backend.app.core import LLMClientSingleton, SQLiteSingleton, embed
import backend.app.prompts.graph_prompts as gp

SYSTEM = gp.SYSTEM_PROMPT
USER_TPL = gp.USER_PROMPT_TEMPLATE

async def extract_entities(chunks: list[str]):
    client = LLMClientSingleton()
    for chunk in chunks:
        prompt = [
            {"role": "system", "content": SYSTEM},
            {"role": "user",   "content": USER_TPL.format(text=chunk)}
        ]
        json_line = ""
        async for delta in client.stream_chat(prompt, max_tokens=1000, temperature=0.3):
            json_line += delta
        rows = json.loads(json_line)
        _insert_graph_rows(rows)

def _insert_graph_rows(rows):
    con = SQLiteSingleton()
    for obj in rows:
        head_id = _get_or_insert_entity(obj["head"], obj["head_type"])
        tail_id = _get_or_insert_entity(obj["tail"], obj["tail_type"])
        con.execute(
            "INSERT OR IGNORE INTO relation(head_id, tail_id, rel_type) VALUES(?,?,?)",
            (head_id, tail_id, obj["relation"]),
        )
    con.commit()
```

#### Dedup Logic

```python
def _get_or_insert_entity(surface: str, typ: str) -> int:
    con = SQLiteSingleton()
    cur = con.execute("SELECT id, embedding FROM entity WHERE type=?",
                      (typ,))
    vec_new = embed(surface)[0]
    for row in cur.fetchall():
        if cosine(row["embedding"], vec_new) >= get_config().ENTITY_SIM:   # 0.90
            return row["id"]
    cur = con.execute(
        "INSERT INTO entity(surface, type, embedding) VALUES(?,?,?)",
        (surface, typ, vec_new)
    )
    return cur.lastrowid
```

### 7  Batch Orchestrator (`pipeline.py`)

```python
def process_all():
    for pdf in get_config().INPUT_DIR.glob("*.pdf"):
        pages = load_pages(pdf)
        chunks = sum((chunk_page(p) for p in pages), [])
        add_chunks(chunks, pdf.stem)
        asyncio.run(extract_entities(chunks))
```

Add logging + `yield {"phase":"..."}` to feed the UI.

---

## 📝 Validation Script

```bash
python - <<'PY'
from backend.app.ingest.pipeline import process_all
process_all()
from backend.app.core import ChromaSingleton, SQLiteSingleton
print("Chunks:", ChromaSingleton()._collection.count())
print("Entities:", SQLiteSingleton().execute("SELECT COUNT(*) FROM entity").fetchone()[0])
PY
```

Expect **non‑zero** counts.

---

## 🕑 Estimated Effort

| Task | Time (min) |
|------|------------|
| Endpoint scaffolding | 10 |
| Reset + loader | 5 |
| Semantic chunking tuning | 15 |
| Vector insert & tests | 8 |
| Entity extraction & dedup | 20 |
| Progress & validation | 5 |
| **Total** | **~1 hr** |

---

## 🚑 Troubleshooting & Tips

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Chunks extremely short/long | Splitter thresholds off | Adjust `breakpoint_percentile_threshold` (50–70) |
| `sqlite3.InterfaceError: Error binding parameter` | Attempting to pass list as BLOB | Serialize embeddings with `array('f')` bytes |
| LLM times out on big chunk | Chunk exceeds 3 k tokens | Limit chunk length pre‑prompt |
| Duplicate entity rows | Cosine threshold too high | Lower to 0.88 or normalise embeddings |

---

## 📝 Deliverables

1. **`backend/app/ingest/`** package: `loader.py`, `chunker.py`, `pipeline.py`, `reset.py`  
2. API router **`ingest.py`** and registration in `main.py`  
3. Populated `vector_store/` and `graph.db` after sample run  
4. Git tag **`phase‑3`**

---

_When the validation script prints non‑zero counts and the UI displays real‑time progress for `/upload`, **Phase 3 is complete**. Proceed to **Phase 4 – Query Workflow**._
