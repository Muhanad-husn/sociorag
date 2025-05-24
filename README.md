# SocioGraph

A system for analyzing and visualizing social dynamics in texts.

## Setup Instructions

1. **Prerequisites**
   - Python 3.12.9
   - [Miniconda](https://docs.conda.io/en/latest/miniconda.html) ≥ 23.10
   - Git 2.30+

2. **Environment Setup**
   ```bash
   # Create and activate conda environment
   conda create -y -n sociograph python=3.12.9
   conda activate sociograph

   # Install dependencies
   python -m pip install --upgrade pip
   pip install fastapi uvicorn[standard] langchain chromadb sqlite-vec \
               tiktoken openrouter-client sentence-transformers llama-index \
               pydantic markdown-it-py weasyprint cairocffi spacy

   # Download spaCy model
   python -m spacy download en_core_web_sm
   ```

3. **Repository Structure**
   ```
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
