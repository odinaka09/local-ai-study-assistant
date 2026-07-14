Privacy-Focused AI Study Assistant

A local, privacy-first document processing pipeline and AI assistant built with Python, Ollama, and open-source LLMs. This tool ingests complex academic PDFs and generates structured study guides, summaries, and practice questions entirely offline, ensuring zero data leakage and zero API costs.

    Zero External Dependencies: Runs 100% locally via Ollama, eliminating token-based API costs and cloud data privacy risks.

    Map-Reduce Chunking Pipeline: Automatically splits massive textbooks or lecture notes into logical chunks, extracts key insights recursively, and synthesizes them without hitting token limits or suffering from "Lost in the Middle" syndrome.

    Optimized Document Ingestion: Uses pymupdf4llm to convert dense PDF lecture notes into token-efficient Markdown, drastically reducing computational overhead.

    Interactive HTML & MathJax Export: Outputs clean study guides with native LaTeX mathematical rendering, viewable in any browser and instantly convertible to PDF via Ctrl + P.

🧠 System Architecture: How It Works

The pipeline is divided into modular stages:

    Ingestion & Parsing (ingest_docs.py): The system verifies the target PDF and utilizes PyMuPDF to extract text and format it into Markdown. The Markdown is cached locally to prevent redundant processing.

    Dynamic Chunking (assistant_workflow.py): Splits the document at natural paragraph breaks and processes chunks iteratively through a Map-Reduce framework.

    Local Inference (local_llm.py): Routes context and strict prompt templates to the local Ollama daemon, enforcing rigid formatting for executive summaries, core concepts, LaTeX formulas, and scenario-based practice exams.

🛠️ Tech Stack

    Language: Python 3.10+

    LLM Engine: Ollama (Llama 3 / Mistral)

    Document Processing: PyMuPDF (pymupdf4llm)

    Rendering: Markdown & MathJax

💻 Local Setup

    Install Ollama: Download and install from ollama.com.

    Pull a Model: Open your terminal and run ollama pull llama3.

    Install Dependencies:
    pip install -r requirements.txt

    Run the Assistant:
    python src/assistant_workflow.py --pdf data/sample_lecture.pdf