# SocioGraph — Rebuild Plan (Full Wrap‑Up Report)

This document details every step required to rebuild **SocioGraph** on a single, CPU‑only local machine.  
Follow the phases in sequence; later steps depend on earlier ones.

---

## Phase 0 — Environment & Repository Scaffolding

**Goal:** Create a clean Python workspace and skeleton folder layout.

| Item              | Instruction                                                                                                                                                                           |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Python**        | 1. Install Anaconda or Miniconda.<br>2. `conda create -n sociograph python=3.12.9 && conda activate sociograph`                                                                       |
| **Core packages** | `pip install fastapi uvicorn[standard] langchain chromadb sqlite-vss tiktoken openrouter-client sentence-transformers llama-index pydantic markdown-it-py weasyprint cairocffi spacy` |
| **spaCy model**   | `python -m spacy download en_core_web_sm`                                                                                                                                             |
| **Repo layout**   | ```text                                                                                                                                                                               |
| backend/          |                                                                                                                                                                                       |
| app/              |                                                                                                                                                                                       |

core/        # singletons & config
ingest/      # loaders & chunkers
retriever/   # search pipeline
api/         # FastAPI routers

  tests/
ui/
  src/
resources/
  logo.png
  pdf_theme.css
input/
saved/
vector_store/

| **Version control** | Initialise Git and commit the scaffold. |

---

## Phase 1 — Global Configuration

**Goal:** Centralise all tunables for easy adjustment.

1. Implement a `Config` class in `backend/app/core/config.py`.  
2. Include: data paths, model names, chunk similarity **0.85**, **entity similarity 0.90**, top‑k parameters, PDF theme path, etc.  
3. Support overrides via `.env` **or** `config.yaml`.  
4. Add README notes explaining how to change defaults.

**Deliverable:** Importable `Config` singleton.

---

## Phase 2 — Infrastructure Singletons

**Goal:** Ensure exactly one instance of each heavy resource.

| Singleton            | Purpose                                  | Key Setup                                                   |
| -------------------- | ---------------------------------------- | ----------------------------------------------------------- |
| `LoggerSingleton`    | Consistent logging.                      | `logging.getLogger("sociograph")`; level via `Config`.      |
| `EmbeddingSingleton` | Sentence embedding (`all‑MiniLM‑L6‑v2`). | Expose `.embed(texts)`.                                     |
| `ChromaSingleton`    | Persistent chunk store.                  | `persist_directory = Config.VECTOR_DIR`; pass embedding fn. |
| `SQLiteSingleton`    | Graph DB + `sqlite‑vss` for ANN.         | File at `Config.GRAPH_DB`; tables `entity`, `relation`.     |
| `LLMClientSingleton` | OpenRouter wrapper.                      | Reads API key from env; async streaming.                    |
| `NLPSingleton`       | spaCy noun extractor.                    | `spacy.load("en_core_web_sm")`.                             |

**Deliverable:** `backend/app/core/singletons.py`

---

## Phase 3 — Ingestion Pipeline

**Goal:** Convert PDF uploads into searchable chunks + graph.

| Step                      | Action                                                                                 |
| ------------------------- | -------------------------------------------------------------------------------------- |
| 3.1 **Reset**             | `/reset` endpoint deletes `vector_store/`, clears DB, and empties `input/` & `saved/`. |
| 3.2 **Upload**            | `/upload` saves PDFs into `input/`; warns that corpus overwrite is allowed.            |
| 3.3 **Semantic chunking** | Implement per *Semantic_Chunking.md* (buffer merge, max tokens).                       |
| 3.4 **Vector index**      | Embed each chunk; add to Chroma (similarity checked later).                            |
| 3.5 **Entity extraction** | Prompt LLM (see `graph_prompts.py`) and parse JSON relations.                          |
| 3.6 **Entity dedup**      | Reuse entity if cosine ≥ **0.90**, else insert.                                        |
| 3.7 **Batch commits**     | Commit every ~100 entities to keep SQLite fast.                                        |

**Deliverables:**  

* Populated `vector_store/`  
* `graph.db` with `entity` & `relation` rows

---

## Phase 4 — Query Workflow

**Goal:** Retrieve relevant context for answering.

1. **Detect language** (langdetect).  
2. **Translate** Arabic → English (Helsinki).  
3. **Chunk retrieval**: embed query, cosine ≥ 0.85, `top_k = 100`.  
4. **Cross‑encoder rerank** (`cross-encoder/ms-marco-MiniLM-L-6-v2`), keep top 15.  
5. **Graph retrieval**: spaCy nouns → ANN over entities (≥ 0.90) → related triples.  
6. **Context merge**: combine texts + triples, trim to ~40 % of model context.

**Deliverable:** `retrieve_context(query)`

---

## Phase 5 — Answer Generation & PDF Export

**Goal:** Produce bilingual answers + branded PDF.

1. Build prompts via `answer_prompt.py`; stream from `meta-llama/llama-3.3-70b-instruct:free`.  
2. Translate English markdown → Arabic (`mistral-nemo`).  
3. **PDF pipeline**  
   - Markdown → HTML (`markdown-it-py`).  
   - Jinja template wraps header (logo) & footer.  
   - Stylesheet: `resources/pdf_theme.css`.  
   - Render with **WeasyPrint** (pure‑Python).  
4. Save PDF to `saved/`, return link.

---

## Phase 6 — FastAPI Back‑End

**Goal:** Expose REST / streaming API.

| Route              | Purpose                             |
| ------------------ | ----------------------------------- |
| `POST /upload`     | Upload PDF & start ingest.          |
| `POST /process`    | (Optional) manually trigger ingest. |
| `POST /search`     | Stream bilingual answer (SSE).      |
| `POST /reset`      | Call Phase 3.1.                     |
| `GET  /history`    | List past queries.                  |
| `GET  /saved/{id}` | Download stored PDF.                |

Start server: `uvicorn backend.app.main:app --reload`

---

## Phase 7 — Preact / Tailwind Front‑End

**Goal:** Lightweight local UI.

- **Pages:** Home/Search, History, Saved, Settings  
- **Key elements:** file uploader, query box, sliders (`top_k`), language toggle, Sonner toasts  
- Visual consistency via same colours/fonts as `pdf_theme.css`.

---

## Phase 8 — Testing & Utilities

**Goal:** Ensure repeatability.

- **Unit tests** (`pytest`) for singletons, ingest, retrieval.  
- **Fixture PDF** in `tests/fixtures/`.  
- CLI helpers: `python -m sociograph.reset`, `python -m sociograph.ingest input/*.pdf`.  
- Optional GitHub Actions CI (runs tests).

---

## Phase 9 — Documentation

**Goal:** Smooth onboarding.

- **README.md** (quick‑start, FAQs).  
- **docs/architecture.md** (singleton diagram).  
- **CHANGELOG.md** (version history).

---

## Final Checklist

- [ ] Conda env created & packages installed  
- [ ] Scaffold committed to Git  
- [ ] `Config` centralised (entity sim 0.90)  
- [ ] All singletons implemented  
- [ ] Ingestion works with sample PDF  
- [ ] Query pipeline returns context  
- [ ] PDF generation branded & stored  
- [ ] FastAPI server reachable on `localhost:8000`  
- [ ] Preact UI builds & connects  
- [ ] Unit tests green  
- [ ] Documentation complete  

When every box is checked, **SocioGraph** is fully rebuilt and ready for local use.
