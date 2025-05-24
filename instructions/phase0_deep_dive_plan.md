# **SocioGraph Rebuild — Phase 0 Deep‑Dive Plan**

> **Objective:** Establish a reproducible Python environment and a clean repository scaffold that every later phase can rely on.

---

## 🎯 Outcomes

| ID | Outcome | Acceptance Criteria |
|----|---------|---------------------|
| O‑0.1 | Conda env `sociograph` (Python 3.12.9) is created and **activates without errors**. | `python --version` → `3.12.9` |
| O‑0.2 | All **core runtime packages** are installed at the pinned versions listed below. | `pip list` shows packages; `python -c "import fastapi"` succeeds |
| O‑0.3 | spaCy English model `en_core_web_sm` is downloaded and loadable. | `python -m spacy info en_core_web_sm` |
| O‑0.4 | Repository **folder layout** exists exactly as specified. | `tree -L 2` matches layout |
| O‑0.5 | Git repository initialised with first commit tagged `phase‑0`. | `git log --oneline` shows initial commit |

---

## ⚙️ Prerequisites

1. **Operating System:** Windows 10+, macOS 12+, or any modern Linux distro  
2. **Disk space:** ≥ 5 GB free (vector store & PDFs will grow later)  
3. **Privileges:** Ability to install Conda and Python packages, and initialise Git  
4. **Tools:**  
   - [Miniconda ≥ 23.10](https://docs.conda.io/en/latest/miniconda.html) (preferred for lean footprint)  
   - Git 2.30+  
   - Optional IDE (VS Code recommended)

---

## 🛠️ Step‑by‑Step Procedure

### 1  Install & Validate Conda

```bash
# macOS/Linux
brew install --cask miniconda   # or download installer from the website
conda init "$(basename "$SHELL")" && exec "$SHELL"

# Windows (PowerShell, run as admin)
winget install -e --id Anaconda.Miniconda3
```

Verify:

```bash
conda --version      # e.g. conda 24.1.0
```

### 2  Create and Activate the Environment

```bash
conda create -y -n sociograph python=3.12.9
conda activate sociograph
```

*(Tip: add `conda activate sociograph` to your shell profile for auto‑activation when you `cd` into the repo.)*

### 3  Upgrade `pip` and Install Core Packages

```bash
python -m pip install --upgrade pip

pip install fastapi uvicorn[standard] langchain chromadb sqlite-vss \
           tiktoken openrouter-client sentence-transformers llama-index \
           pydantic markdown-it-py weasyprint cairocffi spacy
```

> **Why these packages?** They satisfy the runtime dependencies for ingestion (LangChain, ChromaDB, sqlite‑vss), retrieval (sentence‑transformers, tiktoken), serving (FastAPI + Uvicorn), answer generation (openrouter‑client), and PDF export (markdown‑it‑py, WeasyPrint, cairocffi). fileciteturn0file8

### 4  Fetch spaCy Model

```bash
python -m spacy download en_core_web_sm
```

### 5  Bootstrap the Repository Scaffold

```bash
# Clone or initialise the repo
git init sociograph && cd sociograph

# Create the folder tree
mkdir -p backend/app/{core,ingest,retriever,api} backend/tests \
         ui/src resources input saved vector_store

# Add branding asset placeholder
curl -L -o resources/logo.png "https://dummyimage.com/600x200/000/fff&text=SocioGraph"
```

**Recommended `.gitignore`**

```
# Python
__pycache__/
*.py[cod]
*.egg-info/

# Conda & virtualenv
.env
.venv
*.conda

# Runtime dirs
vector_store/
input/
saved/

# OS
.DS_Store
Thumbs.db
```

Commit:

```bash
git add .
git commit -m "Phase‑0 scaffold and environment setup"
git tag phase-0
```

### 6  (Optional) Developer Quality Tools

```bash
pip install black isort flake8 pre-commit
pre-commit install
```

Add `.pre-commit-config.yaml` to enforce formatting before every commit.

### 7  Validation Checks

```bash
# Environment sanity
python - <<'PY'
import fastapi, langchain, chromadb, spacy
print("✅ Core libraries import OK")
PY

# Directory tree
tree -L 2

# Git status
git status
```

All checks pass ⇒ Phase 0 **complete**.

---

## 📝 Deliverables

1. **Conda environment file** (optional):  

   ```bash
   conda env export --from-history > environment.yml
   ```

2. **Repository scaffold** committed and tagged `phase‑0`.  
3. **Documentation:** update `README.md` with instructions above for team onboarding.

---

## 🕑 Estimated Effort

| Task | Time (min) |
|------|------------|
| Install Conda | 5–10 |
| Environment creation & package install | 8–12 |
| spaCy model download | 2 |
| Repo scaffold & Git setup | 5 |
| Validation | 3 |
| **Total** | **~25 min** |

---

## 🚑 Troubleshooting & Tips

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `sqlite3.OperationalError: no such module: vss0` | `sqlite-vss` not loaded | Ensure the `sqlite-vss` wheel is installed; restart Python. |
| `ModuleNotFoundError: cairocffi` during WeasyPrint import | Cairo backend missing | The **Phase 0** install includes `cairocffi`; rerun `pip install`. |
| Conda slow package solve | Outdated `conda` | `conda update -n base -c defaults conda` |

---

_Proceed to **Phase 1 – Global Configuration** after all deliverables pass review._
