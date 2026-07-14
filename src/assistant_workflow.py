import os
import argparse
import logging
import pathlib
from ingest_docs import convert_pdf_to_markdown
from local_llm import query_local_assistant
import markdown
from xhtml2pdf import pisa


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def chunk_text(text: str, max_chars: int = 15000) -> list[str]:
    """Splits text into chunks at natural paragraph breaks to avoid cutting sentences in half."""
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for p in paragraphs:
        if len(current_chunk) + len(p) < max_chars:
            current_chunk += p + '\n\n'
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = p + '\n\n'
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

def generate_study_guide(pdf_path: str, output_md_path: str, model_name: str, num_bullets: int, num_questions: int):
    """Processes a PDF document and generates a study guide using a Map-Reduce chunking pipeline."""
    
    # 1. Validate & Convert
    if not os.path.exists(pdf_path):
        logging.error(f"Source PDF not found at: {pdf_path}")
        return

    if not os.path.exists(output_md_path):
        logging.info(f"Converting {pdf_path} to Markdown...")
        try:
            document_text = convert_pdf_to_markdown(pdf_path, output_md_path)
        except Exception as e:
            logging.error(f"Failed to convert PDF: {e}")
            return
    else:
        logging.info(f"Loading existing Markdown from {output_md_path}...")
        with open(output_md_path, "r", encoding="utf-8") as f:
            document_text = f.read()

    # 2. Chunk the Document
    chunks = chunk_text(document_text)
    logging.info(f"Document split into {len(chunks)} logical chunks for safe processing.")

    # 3. Map Phase: Extract notes from each chunk
    extracted_notes = ""
    extraction_prompt = """
    You are an AI data extractor. Extract core concepts, definitions, and formulas from the text. 
    CRITICAL: You will see garbled math from PDF extraction (e.g., "SD (x) / V ¯ x" or "N 3 - x ~~ x ~~"). You MUST translate these broken strings into clean LaTeX (e.g., \frac{SD(x)}{\bar{x}}). Do not output the broken symbols.
    """
    for i, chunk in enumerate(chunks):
        logging.info(f"Mapping chunk {i+1}/{len(chunks)}... (Extracting raw data)")
        try:
            user_msg = f"Extract data from this text:\n\n{chunk}"
            chunk_summary = query_local_assistant(system_prompt=extraction_prompt, user_content=user_msg, model_name=model_name)
            extracted_notes += f"\n\n--- Data from Section {i+1} ---\n{chunk_summary}"
        except Exception as e:
            logging.error(f"Failed to process chunk {i+1}: {e}")
            return

    # 4. Reduce Phase: Final Synthesis
    logging.info("Reduce Phase: Synthesizing extracted data into the final study guide...")
    
    system_prompt = f"""
    You are an expert AI tutor. You MUST output EXACTLY 6 sections. Do not stop generating until Section 6 is finished.
    
    ## 1. Executive Summary
    Provide a 3-4 sentence overview.
    
    ## 2. Key Concepts & Core Logic
    Extract exactly {num_bullets} detailed bullet points.
    
    ## 3. Formulas, Syntax & Code Blocks
    Use standard LaTeX syntax enclosed in $$ (e.g., $$ \\sigma^2 = \\frac{{\\sum (x_i - \\mu)^2}}{{N}} $$). 
    
    ## 4. Common Pitfalls & Edge Cases
    Identify 2-3 common errors.
    
    ## 5. Practice Exam
    Generate {num_questions} questions. YOU MUST FORMAT EXACTLY LIKE THIS:
    1. [Question text]
    A) [Option]
    B) [Option]
    C) [Option]
    D) [Option]
    
    ## 6. Answer Key
    YOU MUST COMPLETE THIS SECTION. Provide all {num_questions} answers. FORMAT EXACTLY LIKE THIS:
    1. [Letter] - [1-2 sentence explanation]
    2. [Letter] - [1-2 sentence explanation]
    """
    
    try:
        user_prompt = f"Synthesize these extracted notes into the final study guide:\n\n{extracted_notes}"
        final_response = query_local_assistant(system_prompt=system_prompt, user_content=user_prompt, model_name=model_name)
        
        print("\n" + "="*50)
        print("🎓 AI STUDY GUIDE GENERATED")
        print("="*50 + "\n")
        print(final_response)
        
        # Save to disk
        pdf_name = pathlib.Path(pdf_path).stem
        save_path = f"data/{pdf_name}_study_guide.md"
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(final_response)
        
        logging.info(f"Study guide successfully saved to {save_path}")

        print("\n" + "-"*50)
        export_choice = input("Would you like to export this study guide as an interactive HTML page? (y/n): ").strip().lower()
        
        if export_choice == 'y':
            html_save_path = f"data/{pdf_name}_study_guide.html"
            logging.info(f"Generating HTML at {html_save_path}...")
            
            # Convert Markdown to HTML
            html_content = markdown.markdown(final_response, extensions=['tables', 'fenced_code'])
            
            # Wrap in CSS and inject the MathJax engine
            styled_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>AI Study Guide</title>
                <!-- This script instantly renders all LaTeX on the page -->
                <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 15px; line-height: 1.6; color: #333; max-width: 850px; margin: 40px auto; padding: 20px; }}
                    h1, h2, h3 {{ color: #2c3e50; }}
                    h2 {{ border-bottom: 2px solid #eee; padding-bottom: 5px; margin-top: 30px; }}
                    code {{ background-color: #f8f9fa; padding: 3px 6px; border-radius: 4px; font-family: "Courier New", Courier, monospace; color: #d63384; }}
                    pre {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; border: 1px solid #e9ecef; }}
                    pre code {{ color: #333; background-color: transparent; }}
                    ul, ol {{ margin-bottom: 15px; }}
                    li {{ margin-bottom: 8px; }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            with open(html_save_path, "w", encoding="utf-8") as f:
                f.write(styled_html)
                
            logging.info(f"✅ HTML successfully generated at {html_save_path}")
            logging.info("💡 HINT: Double-click the HTML file to open it in your browser to see the math. Press Ctrl+P to save it as a perfect PDF!")
        else:
            logging.info("Skipping HTML generation.")
            
    except Exception as e:
        logging.error(f"Final generation failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local AI Study Assistant Pipeline")
    parser.add_argument("--pdf", type=str, required=True, help="Path to the source PDF file")
    parser.add_argument("--out", type=str, default="data/output.md", help="Path to save the Markdown output")
    parser.add_argument("--model", type=str, default="llama3", help="Ollama model to use for inference")
    parser.add_argument("--bullets", type=int, default=10, help="Number of summary bullet points to generate")
    parser.add_argument("--questions", type=int, default=10, help="Number of practice questions to generate")
    args = parser.parse_args()
    
    generate_study_guide(args.pdf, args.out, args.model, args.bullets, args.questions)