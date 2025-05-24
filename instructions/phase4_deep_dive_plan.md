# **SocioGraph Rebuild — Phase 4 Deep‑Dive Plan**

> **Objective:** Build a robust **query workflow** that detects the user’s language, translates Arabic → English when needed, retrieves the most relevant vector chunks **and** graph triples, reranks with a cross‑encoder, and merges everything into a trimmed context block ready for answer generation.

---

## 🎯 Outcomes

| ID | Outcome | Acceptance Criteria |
|----|---------|---------------------|
| O‑4.1 | `normalize_query(text)` returns a tuple `(lang, text_en)` where `lang ∈ {"en","ar"}`. | Arabic input is translated to English; English remains unchanged. |
| O‑4.2 | `retrieve_chunks()` returns ≤ `Config.TOP_K` texts whose cosine ≥ `Config.CHUNK_SIM` (0.85). | `len(chunks) ≤ 100` and all similarities logged. |
| O‑4.3 | `rerank_chunks()` keeps exactly `Config.TOP_K_RERANK` (15) highest‑scoring docs using **cross‑encoder/ms‑marco‑MiniLM‑L‑6‑v2**. | Returned docs are ordered by descending score. fileciteturn4file7 |
| O‑4.4 | `retrieve_triples()` fetches graph triples whose entity similarity ≥ `Config.GRAPH_SIM` (0.95). | SQL ANN search proves at least one triple for noun entities. |
| O‑4.5 | `merge_context()` trims combined tokens to ≤ 40 % of answer‑model context window, preserving order *chunks → triples*. | Token count verified via `tiktoken`. |
| O‑4.6 | Public API `retrieve_context(query: str) -> dict` returns `{chunks, triples, lang}` in < 1.5 s on laptop. | Pytest timer passes. |

---

## 📋 Pipeline Overview  fileciteturn4file2

```
Query
  │
  ├─▶ Language Detect (langdetect)
  │     └─▶ Arabic? —► Helsinki-NLP ⇢ English  fileciteturn4file17
  │
  ├─▶ Embed query (Sentence‑Txf)
  │
  ├─▶ Vector Search (Chroma, sim≥0.85, k=100)
  │           └─▶ Cross‑Encoder Rerank ➟ top‑15  fileciteturn4file7
  │
  ├─▶ Noun Extraction (spaCy)
  │           └─▶ ANN search on `entity` (sim≥0.95) ➟ triples
  │
  └─▶ Merge & Trim (tiktoken, 40 %)
                    ↓
           **Context Package**
```

---

## ⚙️ Prerequisites

```bash
pip install langdetect transformers tiktoken sentence-transformers
```

* Phases 0‑3 completed (env, singletons, ingest data present).  
* Set `OPENROUTER_API_KEY` for downstream phases (not strictly required here).  

---

## 🛠️ Step‑by‑Step Implementation

### 1  Module Layout

```
backend/app/retriever/
  __init__.py          # expose retrieve_context
  language.py          # detect & translate
  vector.py            # chunk retrieval + rerank
  graph.py             # noun→triples
  merge.py             # token‑aware merge
  pipeline.py          # orchestrator (retrieve_context)
```

Register tests under `backend/tests/test_retriever.py`.

---

### 2  Language Detection & Translation (`language.py`)

```python
from langdetect import detect
from transformers import MarianMTModel, MarianTokenizer
from backend.app.core import LoggerSingleton

_tok, _model = None, None

def _load_helsinki():
    global _tok, _model
    if _tok is None:
        _tok = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-tc-big-ar-en")
        _model = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-tc-big-ar-en")

def normalize_query(text: str) -> tuple[str, str]:
    lang = detect(text)
    if lang == "ar":
        _load_helsinki()
        inputs = _tok(text, return_tensors="pt")
        output = _model.generate(**inputs, max_length=256, num_beams=4, early_stopping=True)
        text_en = _tok.decode(output[0], skip_special_tokens=True)
        LoggerSingleton().info("Translated AR → EN: %s", text_en)
        return "ar", text_en
    return "en", text
```

---

### 3  Vector Retrieval & Cross‑Encoder Rerank (`vector.py`)

```python
from langchain.vectorstores import Chroma
from sentence_transformers import CrossEncoder
from backend.app.core import ChromaSingleton, embed, LoggerSingleton, get_config

_cfg = get_config()
_reranker = CrossEncoder(_cfg.RERANKER_MODEL, max_length=512)

def retrieve_chunks(query_emb):
    vectordb = ChromaSingleton()
    docs = vectordb.similarity_search_by_vector(
        query_emb, k=_cfg.TOP_K, include=["embeddings", "metadatas"]
    )
    return docs

def rerank_chunks(query: str, docs):
    pairs = [(query, d.page_content) for d in docs]
    scores = _reranker.predict(pairs)
    ranked = sorted(zip(docs, scores), key=lambda t: t[1], reverse=True)
    return [d for d, _ in ranked[: _cfg.TOP_K_RERANK]]
```

---

### 4  Graph Triples Retrieval (`graph.py`)

```python
from backend.app.core import NLPSingleton, SQLiteSingleton, embed, get_config
from array import array

_cfg = get_config()
_nlp = NLPSingleton()

def _fetch_entity_hits(noun: str):
    con = SQLiteSingleton()
    vec = embed(noun)[0]          # 384‑dim list
    sql = "SELECT id, surface, embedding FROM entity USING vss0 WHERE vss_search(embedding, ?) LIMIT 5"
    rows = con.execute(sql, (array("f", vec).tobytes(),)).fetchall()
    return [r for r in rows if cosine(r["embedding"], vec) >= _cfg.GRAPH_SIM]

def retrieve_triples(query_en: str):
    nouns = [t.text for t in _nlp(query_en) if t.pos_ == "NOUN"]
    con = SQLiteSingleton()
    triples = []
    for noun in nouns:
        for hit in _fetch_entity_hits(noun):
            triples.extend(con.execute(
                "SELECT * FROM relation WHERE head_id=? OR tail_id=?", (hit["id"], hit["id"])
            ).fetchall())
    return triples
```

---

### 5  Context Merge & Token Budgeting (`merge.py`)

```python
import tiktoken
from backend.app.core import get_config

_enc = tiktoken.encoding_for_model("gpt-4o")         # safe default

def merge_context(chunks, triples, context_window=8192):
    texts = [d.page_content for d in chunks]
    triple_strs = [f"{t['head_id']} {t['rel_type']} {t['tail_id']}" for t in triples]
    combined = texts + triple_strs
    limit = int(context_window * get_config().MAX_CONTEXT_FRACTION)   # 0.4
    out = []
    tokens = 0
    for item in combined:
        t = len(_enc.encode(item))
        if tokens + t > limit:
            break
        out.append(item)
        tokens += t
    return out
```

---

### 6  Orchestrator (`pipeline.py`)

```python
from backend.app.retriever.language import normalize_query
from backend.app.retriever.vector import retrieve_chunks, rerank_chunks
from backend.app.retriever.graph import retrieve_triples
from backend.app.retriever.merge import merge_context
from backend.app.core import embed

def retrieve_context(user_query: str):
    lang, query_en = normalize_query(user_query)
    q_vec = embed(query_en)[0]
    raw_chunks = retrieve_chunks(q_vec)
    chunks = rerank_chunks(query_en, raw_chunks)
    triples = retrieve_triples(query_en)
    context = merge_context(chunks, triples)
    return {"lang": lang, "chunks": chunks, "triples": triples, "context": context}
```

Expose `retrieve_context` in `backend/app/retriever/__init__.py`.

---

### 7  Unit Tests (`test_retriever.py`)

```python
import time, pytest
from backend.app.retriever import retrieve_context

@pytest.mark.parametrize("q", ["ما هي عاصمة مصر؟", "What is social graph?"])
def test_retrieval(q):
    start = time.time()
    res = retrieve_context(q)
    assert "context" in res and len(res["context"]) > 0
    assert res["lang"] in {"en","ar"}
    assert time.time() - start < 1.5
```

Run `pytest -q`.

---

## 📝 Validation Script

```bash
python - <<'PY'
from backend.app.retriever import retrieve_context
print(retrieve_context("Explain knowledge graphs in AI")["context"][:3])
PY
```

Expect first three context items printed.

---

## 🕑 Estimated Effort

| Task | Time (min) |
|------|------------|
| Language detect & translate | 10 |
| Vector retrieval & rerank | 15 |
| Graph triples | 15 |
| Merge + token budget | 5 |
| Orchestrator & tests | 10 |
| Docs & README | 5 |
| **Total** | **~1 hr** |

---

## 🚑 Troubleshooting & Tips

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Wrong language detected | `langdetect` heuristic weak for short text | Require ≥ 4 tokens before detection; else bypass translate |
| Rerank latency high | HF model on CPU | Batch size 16; reduce `TOP_K` |
| No triples returned | Nouns not found in graph | Lower `GRAPH_SIM` to 0.90 or fallback to fallback heuristics |
| Context too long | Large triples list | Drop least‑similar chunks before trimming triples |

---

## 📝 Deliverables

1. **`backend/app/retriever/`** package with modules above.  
2. Public function **`retrieve_context`** returning merged context.  
3. Unit & validation tests passing.  
4. README “Query Workflow” section.  
5. Git tag **`phase‑4`**.

---

_When `retrieve_context()` returns a non‑empty context for both English and Arabic queries, and tests pass in < 1.5 s, **Phase 4 is complete**. Next stop: **Phase 5 – Answer Generation & PDF Export**._

