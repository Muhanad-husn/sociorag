# **SocioGraph Rebuild — Phase 5 Deep‑Dive Plan**

> **Objective:** Turn the context package from Phase 4 into a fully formatted **answer** (Markdown → HTML → PDF), stream it to the UI in real‑time, and archive every Q&A set for later review.

---

## 🎯 Outcomes

| ID    | Outcome                                                                                                        | Acceptance Criteria                                                |
| ----- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| O‑5.1 | `generate_answer(query, context)` returns a **Markdown** answer with numbered citations like <sup>[1]</sup>.   | Unit test parses answer for `\[\d+]` patterns.                     |
| O‑5.2 | At least **80 %** of citations correspond to retrieved chunk or triple IDs.                                    | Alignment test passes on sample docs.                              |
| O‑5.3 | `/ask` endpoint streams answer tokens (Server‑Sent Events) to UI with `<span data-id="tok">…</span>` wrappers. | UI displays typing effect (see UI overview). fileciteturn5file6 |
| O‑5.4 | After generation, a **PDF** version is stored in `saved/<<timestamp>>.pdf` following brand CSS.                | File exists & opens.                                               |
| O‑5.5 | Q&A metadata logged in `saved/history.jsonl` (query, answer_path, timestamp, tokens).                          | Entry appended after every /ask.                                   |
| O‑5.6 | Generating an answer for a 2‑sentence query finishes in **< 15 s** with CPU.                                   | Timer test passes.                                                 |

---

## 📋 Component Diagram  instructions\sociograph_rebuild_plan.md

```
 /ask  ──► retrieve_context()         ─┐
          (Phase 4)                   │
                                      ▼           ┌────────────┐
                            tiktoken budget ──►  │ answer_prompt│
                                      ▼           └────────────┘
                            OpenRouter Chat  ───►  gpt‑4o‑mini  fileciteturn5file4
                                      ▼
                       markdown stream (SSE) ◄───┘
                                      ▼
                markdown-it-py  →  HTML  →  WeasyPrint  →  PDF
```

---

## ⚙️ Prerequisites

```bash
pip install markdown-it-py weasyprint cairocffi sse-starlette tiktoken
```

* `answer_prompt.py` with prompt helper functions is present. instructions\answer_prompt.py  
* Brand CSS file created in Phase 0 (`resources/pdf_theme.css`).  
* Phases 0‑4 complete.

---

## 🛠️ Step‑by‑Step Implementation

### 1  Prompt Helper (`backend/app/answer/prompt.py`)

Reuse logic from **`answer_prompt.py`**: functions `build_system_prompt()`, `build_user_prompt()`, and citation post‑processor. fileciteinstructions\answer_prompt.py

```python
from backend.app.prompts.answer_prompt import (
    build_system_prompt,
    build_user_prompt,
    attach_citations,
)
```

### 2  Answer Generator (`generator.py`)

```python
import asyncio, time
from backend.app.core import LLMClientSingleton, LoggerSingleton, get_config
from backend.app.answer.prompt import (
    build_system_prompt, build_user_prompt, attach_citations
)

_cfg = get_config()

async def generate_answer(query: str, context_items: list[str]):
    system_msg = {"role": "system", "content": build_system_prompt()}
    user_msg   = {"role": "user",  "content": build_user_prompt(query, context_items)}
    client = LLMClientSingleton()
    answer_md = ""
    async for delta in client.stream_chat(
        [system_msg, user_msg],
        model=_cfg.ANSWER_LLM_MODEL,
        max_tokens=1024,
        temperature=0.2,
        stream=True,
    ):
        answer_md += delta
        yield delta  # stream piece
    final = attach_citations(answer_md, context_items)
    LoggerSingleton().info("Answer length %d chars", len(final))
    return final
```

### 3  API Endpoint (`backend/app/api/qa.py`)

```python
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
from backend.app.retriever import retrieve_context
from backend.app.answer.generator import generate_answer
from backend.app.answer.pdf import save_pdf

router = APIRouter(tags=["qa"])

@router.post("/ask")
async def ask(req: Request):
    body = await req.json()
    query = body["query"]
    ctx = retrieve_context(query)
    async def event_stream():
        async for token in generate_answer(query, ctx["context"]):
            yield {"event": "token", "data": token}
        # after stream closes, persist PDF
    return EventSourceResponse(event_stream())
```

Attach callback to build PDF after generator finishes.

### 4  Markdown → PDF (`pdf.py`)

```python
from markdown_it import MarkdownIt
from weasyprint import HTML, CSS
from datetime import datetime
from backend.app.core import get_config

_cfg = get_config()
_md = MarkdownIt("commonmark", {"html": True, "linkify": True})

def save_pdf(answer_md: str, query: str):
    html_body = _md.render(answer_md)
    html = f"<html><head><meta charset='utf-8'></head><body>{html_body}</body></html>"
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out = _cfg.SAVED_DIR / f"{timestamp}.pdf"
    CSS_PATH = _cfg.PDF_THEME
    HTML(string=html, base_url=".").write_pdf(out, stylesheets=[CSS(str(CSS_PATH))])
    return out
```

### 5  History Log (`history.py`)

```python
import json, time
from backend.app.core import get_config

_hist = get_config().SAVED_DIR / "history.jsonl"

def append_record(query, pdf_path, token_count):
    with open(_hist, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": time.time(),
            "query": query,
            "pdf": str(pdf_path),
            "tokens": token_count,
        }) + "\n")
```

---

### 6  UI Hook

Front‑end listens to SSE at `/ask`, appends tokens with CSS animation, and offers **“Download answer as PDF”** button linking to `/static/saved/{filename}`. fileciteturn5file6

---

## 📝 Unit Tests (`test_answer.py`)

```python
import pytest, asyncio
from backend.app.answer.generator import generate_answer
from backend.app.retriever import retrieve_context

@pytest.mark.asyncio
async def test_answer_loop():
    ctx = retrieve_context("What is a knowledge graph?")
    md = ""
    async for tok in generate_answer("What is a knowledge graph?", ctx["context"]):
        md += tok
        if len(md) > 100:
            break  # early stop
    assert len(md) > 0
```

---

## 🕑 Estimated Effort

| Task                   | Time (min) |
| ---------------------- | ---------- |
| Prompt & generator     | 20         |
| SSE endpoint & UI glue | 15         |
| Markdown‑HTML‑PDF      | 10         |
| History log            | 5          |
| Tests & docs           | 10         |
| **Total**              | **~1 hr**  |

---

## 🚑 Troubleshooting & Tips

| Symptom                      | Likely Cause               | Fix                                            |
| ---------------------------- | -------------------------- | ---------------------------------------------- |
| PDF missing fonts            | CSS not embedding fonts    | Use `@font-face` with absolute paths           |
| SSE stream disconnects       | Client idle timeout        | Send keep‑alive `:` comments every 10 s        |
| Citations mis‑numbered       | attach_citations regex bug | Ensure stable sorting by first occurrence      |
| Answer truncates prematurely | token budget too low       | Increase `max_tokens` or shorten context merge |

---

## 📝 Deliverables

1. **`backend/app/answer/`** package: `prompt.py`, `generator.py`, `pdf.py`, `history.py`.  
2. API router **`qa.py`** registered.  
3. Updated UI to display live answer and download link.  
4. Tests and validation scripts passing.  
5. Git tag **`phase‑5`**.

---

_When `/ask` streams an answer, the PDF appears in `saved/`, and history logs, **Phase 5 is complete**. Congratulations—SocioGraph now delivers end‑to‑end responses!_
