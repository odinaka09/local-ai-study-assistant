# Privacy-Focused AI Study Assistant

A local, privacy-first document processing pipeline and AI assistant built with Python, Ollama, and open-source LLMs. This tool ingests complex academic PDFs and generates structured study guides, summaries, and practice questions entirely offline, ensuring zero data leakage and zero API costs.
* **Zero External Dependencies:** Runs 100% locally via Ollama, eliminating token-based API costs and cloud data privacy risks.
* **Optimized Document Ingestion:** Uses `pymupdf4llm` to convert dense PDF lecture notes into token-efficient Markdown, drastically reducing the LLM's computational overhead.
* **Hallucination Mitigation:** Employs strict system prompts and low-temperature decoding (`0.2`) to maintain high accuracy during complex context-retrieval tasks.

## 🧠 System Architecture: How It Works
The pipeline is divided into three modular stages:
1. **Ingestion & Parsing (`ingest_docs.py`):** The system verifies the target PDF and utilizes PyMuPDF to extract text and format it into Markdown. The Markdown is cached locally to prevent redundant processing on subsequent runs.
2. **Prompt Orchestration (`assistant_workflow.py`):** The orchestrator constructs a dynamic system prompt based on user-defined CLI arguments (e.g., configuring the exact number of summary bullets).
3. **Local Inference (`local_llm.py`):** The parsed context and system prompt are routed to the local Ollama daemon. The model generates the study guide and outputs the results to the terminal via standard Python logging.

## 🛠️ Tech Stack
* **Language:** Python 3.10+
* **LLM Engine:** Ollama (Llama 3 / Mistral)
* **Document Processing:** PyMuPDF (`pymupdf4llm`)

## 💻 Local Setup

1. **Install Ollama:** Download and install from [ollama.com](https://ollama.com).
2. **Pull a Model:** Open your terminal and run `ollama pull llama3`.
3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt