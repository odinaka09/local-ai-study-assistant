import pathlib
import logging
import pymupdf4llm

def convert_pdf_to_markdown(pdf_path: str, output_md_path: str) -> str:
    """Converts a local PDF file into optimized Markdown format."""
    
    # Extract markdown text
    md_text = pymupdf4llm.to_markdown(pdf_path)
    
    # Persist markdown to disk
    out_file = pathlib.Path(output_md_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(md_text, encoding="utf-8")
    
    logging.info(f"Successfully converted {pdf_path} to Markdown at {output_md_path}")
    
    return md_text