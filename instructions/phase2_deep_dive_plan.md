# Build the Phase 2 deep‑dive Markdown plan and save it for download

phase2_md = """# **SocioGraph Rebuild — Phase 2 Deep‑Dive Plan**

> **Objective:** Provide a _single_ import point—`backend/app/core/singletons.py`—that lazily instantiates and caches every heavy infrastructure object exactly once, so that the whole app can share **one** logger, embedding model, vector store, DB connection, LLM client, and spaCy pipeline.

---

## 🎯 Outcomes

| ID    | Outcome                                                                                                    | Acceptance Criteria                       |
| ----- | ---------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| O‑2.1 | `LoggerSingleton.get()` returns the same `logging.Logger` every call.                                      | `is` identity holds                       |
| O‑2.2 | `EmbeddingSingleton.get()` wraps **all‑MiniLM‑L6‑v2** and embeds lists/str.                                | `len(vec) == 384`                         |
| O‑2.3 | `ChromaSingleton.get()` yields a _persistent_ `Chroma` instance rooted at `Config.VECTOR_DIR`.             | `collection.count()` persists across runs |
| O‑2.4 | `SQLiteSingleton.get()` returns a `sqlite3.Connection` with `vss0` loaded and tables present.              | `PRAGMA table_info(entity)` ok            |
| O‑2.5 | `LLMClientSingleton.get()` exposes an **async** `create_chat(...)` coroutine that streams from OpenRouter. | `async for delta in …` yields chunks      |
| O‑2.6 | `NLPSingleton.get()` returns the same loaded **spaCy** pipeline.                                           | `nlp("hello").doc` works                  |
| O‑2.7 | **Thread‑safety**: objects are created only once even under import‑storm.                                  | Run pytest below                          |

---

## 🗂️ Singletons to Build  fileciteturn2file0

| Name                   | Key Imports                                 | Notes                                                                       |
| ---------------------- | ------------------------------------------- | --------------------------------------------------------------------------- |
| **LoggerSingleton**    | `logging`                                   | Level & formatting driven by `Config.LOG_LEVEL`.                            |
| **EmbeddingSingleton** | `sentence_transformers.SentenceTransformer` | Model name from `Config.EMBEDDING_MODEL`; expose `.embed(texts)`.           |
| **ChromaSingleton**    | `langchain.vectorstores.Chroma`             | Pass embedding fn; set `persist_directory=Config.VECTOR_DIR`.               |
| **SQLiteSingleton**    | `sqlite3`, `vss`                            | Load `sqlite-vss` extension, create `entity` / `relation` tables if absent. |
| **LLMClientSingleton** | `openrouter.client`                         | Async wrapper; reads `OPENROUTER_API_KEY` fileciteturn2file5             |
| **NLPSingleton**       | `spacy`                                     | Pipeline `en_core_web_sm`, disabled ner for speed.                          |

---

## ⚙️ Prerequisites

* Phase 1 complete (`Config` available).
* Packages:  
  
  ```bash
  pip install sentence-transformers langchain chromadb openrouter-client aiosqlite
  ```
