"""Test Script 2: Docling PDF Parsing -> save as .md for comparison.

Docling is IBM's open-source parser -- free, runs locally, no API key.
Compare output side-by-side with LandingAI to decide which to use.

Usage:
    cd D:\\revisto_evidence_aligned_clean
    C:\\Users\\Baku\\miniconda3\\python.exe new_pipeline/tests/test_docling_parse.py

Output:
    new_pipeline/parsed/docling/
    +-- Adrichem_2022.md
    +-- Adrichem_2022_chunks.md
    +-- Adrichem_2022_tables.md
"""

import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add D:\pip_packages (docling + deps, no torch/numpy conflicts)
pip_packages = Path("D:/pip_packages")
if pip_packages.exists():
    sys.path.insert(0, str(pip_packages))

SCRIPT_DIR = Path(__file__).parent
PIPELINE_DIR = SCRIPT_DIR.parent

# Output directory -- inside new_pipeline/parsed/
OUTPUT_DIR = PIPELINE_DIR / "parsed" / "docling"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# PDF directory
PDF_DIR = PIPELINE_DIR / "OneDrive_1_5-6-2026"

# How many PDFs to test
MAX_PDFS = 3


def main():
    try:
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
    except ImportError as e:
        print(f"[ERROR] Docling import failed: {e}")
        print("   Install: pip install docling --target D:\\pip_packages")
        return

    # Use minimal pipeline: no VLM models, no table structure detection
    # This avoids the torchvision incompatibility
    try:
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_table_structure = False
        pipeline_options.do_ocr = False  # Disable OCR too (avoids vision imports)

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
            }
        )
    except Exception as e:
        print(f"[WARN] Custom pipeline failed ({e}), trying default...")
        converter = DocumentConverter()

    pdf_files = sorted(PDF_DIR.glob("*.pdf"))[:MAX_PDFS]
    if not pdf_files:
        print("[ERROR] No PDFs found")
        return

    print(f"Testing with {len(pdf_files)} PDFs:\n")

    for pdf_path in pdf_files:
        print(f"{'='*60}")
        print(f"[PDF] {pdf_path.name} ({pdf_path.stat().st_size / 1024:.0f} KB)")
        print(f"{'='*60}")

        start = time.time()
        try:
            result = converter.convert(str(pdf_path))
        except Exception as e:
            print(f"  [ERROR] Failed: {e}\n")
            continue
        elapsed = time.time() - start

        doc = result.document
        markdown_text = doc.export_to_markdown()

        # ----- File 1: Full markdown -----
        md_path = OUTPUT_DIR / f"{pdf_path.stem}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# {pdf_path.name} (Docling)\n\n")
            f.write(f"**Parse time:** {elapsed:.1f}s\n\n")
            f.write("---\n\n")
            f.write(markdown_text)
        print(f"  [MD] {md_path.name}")

        # ----- File 2: Chunk-by-chunk -----
        chunks_path = OUTPUT_DIR / f"{pdf_path.stem}_chunks.md"
        text_count = 0
        table_count = 0
        figure_count = 0
        chunk_index = 0

        with open(chunks_path, "w", encoding="utf-8") as f:
            f.write(f"# {pdf_path.name} -- Docling Chunks\n\n")
            f.write(f"**Parse time:** {elapsed:.1f}s\n\n---\n\n")

            for item, _level in doc.iterate_items():
                chunk_index += 1
                item_type = type(item).__name__

                if "Table" in item_type:
                    table_count += 1
                    f.write(f"### Chunk {chunk_index} -- `table`\n\n")
                    if hasattr(item, "export_to_markdown"):
                        f.write("```\n" + item.export_to_markdown() + "\n```\n\n")
                    elif hasattr(item, "text"):
                        f.write("```\n" + item.text + "\n```\n\n")
                elif "Picture" in item_type or "Figure" in item_type:
                    figure_count += 1
                    f.write(f"### Chunk {chunk_index} -- `figure`\n\n")
                    caption = getattr(item, "caption", None)
                    if caption:
                        f.write(f"*Caption: {caption}*\n\n")
                    if hasattr(item, "text") and item.text:
                        f.write(item.text + "\n\n")
                else:
                    text_count += 1
                    f.write(f"### Chunk {chunk_index} -- `text` ({item_type})\n\n")
                    text = getattr(item, "text", str(item))
                    f.write(text + "\n\n")

                f.write("---\n\n")

            f.write(f"\n## Summary\n\n")
            f.write(f"| Type | Count |\n|------|-------|\n")
            f.write(f"| Text | {text_count} |\n")
            f.write(f"| Table | {table_count} |\n")
            f.write(f"| Figure | {figure_count} |\n")
            f.write(f"| **Total** | **{chunk_index}** |\n")
        print(f"  [MD] {chunks_path.name}")

        # ----- File 3: Tables only -----
        tables_path = OUTPUT_DIR / f"{pdf_path.stem}_tables.md"
        with open(tables_path, "w", encoding="utf-8") as f:
            f.write(f"# {pdf_path.name} -- Tables Only (Docling)\n\n")
            tidx = 0
            for item, _ in doc.iterate_items():
                if "Table" in type(item).__name__:
                    tidx += 1
                    f.write(f"## Table {tidx}\n\n")
                    if hasattr(item, "export_to_markdown"):
                        f.write(item.export_to_markdown())
                    elif hasattr(item, "text"):
                        f.write(item.text)
                    f.write("\n\n---\n\n")
            if tidx == 0:
                f.write("*No tables detected.*\n")
        print(f"  [MD] {tables_path.name}")

        print(f"  [OK] Done in {elapsed:.1f}s: {chunk_index} chunks")
        print(f"     Text:   {text_count}")
        print(f"     Table:  {table_count}")
        print(f"     Figure: {figure_count}")
        print(f"     Markdown: {len(markdown_text)} chars")
        print()

    print(f"\n[DONE] All outputs saved to: {OUTPUT_DIR}")
    print("Compare with LandingAI output in parsed/landingai/!")


if __name__ == "__main__":
    main()
