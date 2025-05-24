# SocioGraph

A system for analyzing and visualizing social dynamics in texts.

## Setup Instructions

1. **Prerequisites**
   - Python 3.12.9
   - [Miniconda](https://docs.conda.io/en/latest/miniconda.html) ≥ 23.10 (recommended)
   - Git 2.30+

2. **Environment Setup**

   Choose one of the following methods:

   ### Using Conda (Recommended)

   ```bash
   # Clone the repository
   git clone <repository-url>
   cd sociograph

   # Create environment from environment.yml
   conda env create -f environment.yml
   conda activate sociograph
   ```   ### Using pip

   ```bash
   # Clone the repository
   git clone <repository-url>
   cd sociograph

   # Create and activate virtual environment
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1  # On Windows
   source .venv/bin/activate     # On Unix/macOS

   # Install dependencies
   python -m pip install --upgrade pip
   pip install -r requirements.txt

   # Download spaCy model (required for both pip and conda installations)
   python -m spacy download en_core_web_sm
   ```

   Note: The `requirements.txt` file contains only the direct dependencies. Using conda with `environment.yml` is recommended as it provides a more complete and tested environment.

3. **Repository Structure**

   ```text
   backend/              # Backend service
     app/
       core/            # Core business logic
       ingest/         # Data ingestion
       retriever/      # Vector store and retrieval
       api/           # FastAPI endpoints
     tests/           # Backend tests
   ui/src/            # Frontend code
   resources/         # Static resources
   input/            # Input data files
   saved/            # Saved models and states
   vector_store/     # Vector embeddings storage
   ```

4. **Development**
   - The project uses Python 3.12.9
   - Main dependencies include FastAPI, LangChain, ChromaDB, and spaCy
   - Vector storage using sqlite-vec for efficient similarity search
   - Frontend development path to be determined in later phases

## License

TBD
