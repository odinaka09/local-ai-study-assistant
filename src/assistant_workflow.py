import os
import argparse
import logging
import pathlib
import re
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
    You are an AI data extractor. Extract the core concepts, mathematical formulas, and technical definitions from this text slice. 
    CRITICAL: If you see messy, garbled text that represents a mathematical equation, translate it into clean LaTeX format. Keep it highly condensed.
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
    
    system_prompt = system_prompt = f"""
    You are an expert AI academic tutor. Analyze the provided extracted lecture notes and generate a highly structured study guide strictly following this format:
    
    ## 1. Executive Summary
    Provide a concise, 3-4 sentence high-level overview of the document's core theme.
    
    ## 2. Key Concepts & Core Logic
    Extract exactly {num_bullets} detailed bullet points explaining the most critical information, not just listing keywords.
    
    ## 3. Formulas, Syntax & Code Blocks
    EXTRACT ALL mathematical formulas, Python syntax, and strict technical definitions. 
    CRITICAL MATH RULE: You MUST format all mathematical formulas using standard LaTeX syntax (e.g., $$ \\sigma^2 = \\frac{{\\sum (x_i - \\mu)^2}}{{N}} $$). Do not output messy unicode.
    
    ## 4. Common Pitfalls & Edge Cases
    Identify 2-3 common misconceptions, edge cases, or frequent errors related to this topic.
    
    ## 5. Practice Exam
    Generate exactly {num_questions} highly technical, scenario-based multiple-choice questions to test deep understanding. 
    CRITICAL EXAM RULE: DO NOT put the answers in this section. Only provide the question and the A/B/C/D options.
    
    ## 6. Answer Key
    Provide the correct answers here. For each answer, you MUST include a detailed 1-2 sentence explanation detailing WHY the answer is correct and the underlying logic. "Because it is the formula" is an unacceptable explanation.
    You MUST output the exact answers to all {num_questions} questions immediately below this heading. Do NOT use placeholders or notes. Format each answer exactly like this:
    1. [Correct Option Letter] - [1-2 sentence logical explanation of WHY it is correct]
    2. [Correct Option Letter] - [1-2 sentence logical explanation of WHY it is correct]
    Do not include introductory or concluding filler text. Output the markdown immediately.
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
        export_choice = input("Would you like to export this study guide as a PDF? (y/n): ").strip().lower()
        
        if export_choice == 'y':
            pdf_save_path = f"data/{pdf_name}_study_guide.pdf"
            logging.info(f"Generating PDF at {pdf_save_path}...")
            
            # Convert Markdown to HTML (enabling tables and code blocks)
            html_content = markdown.markdown(final_response, extensions=['tables', 'fenced_code'])
            
            # Wrap in basic CSS for professional formatting
            styled_html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Helvetica, Arial, sans-serif; font-size: 12px; line-height: 1.5; color: #333; }}
                    h1, h2, h3 {{ color: #111; margin-bottom: 10px; }}
                    h2 {{ border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 20px; }}
                    code {{ background-color: #f4f4f4; padding: 2px 4px; font-family: "Courier New", Courier, monospace; }}
                    pre {{ background-color: #f4f4f4; padding: 10px; white-space: pre-wrap; }}
                    .math-equation {{ 
                        background-color: #eef2f5; 
                        border-left: 4px solid #0056b3; 
                        padding: 10px; 
                        margin: 10px 0; 
                        font-family: "Courier New", Courier, monospace;
                        font-weight: bold;
                    }}
                    ul, ol {{ margin-bottom: 10px; }}
                    li {{ margin-bottom: 5px; }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            # Create the PDF
            with open(pdf_save_path, "w+b") as result_file:
                pisa_status = pisa.CreatePDF(styled_html, dest=result_file)
                
            if pisa_status.err:
                logging.error("PDF generation encountered an error.")
            else:
                logging.info(f"✅ PDF successfully generated at {pdf_save_path}")
        else:
            logging.info("Skipping PDF generation.")
            
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