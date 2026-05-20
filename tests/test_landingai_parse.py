"""Test Script 1: LandingAI PDF Parsing -> save as .md + .json for inspection.

Parses PDFs via LandingAI ADE and saves:
- Full markdown (.md) for visual inspection
- Chunk-by-chunk breakdown (.md) with types, pages, bboxes
- Full API response (.json) with grounding, splits, metadata

Usage:
    cd D:\\revisto_evidence_aligned_clean
    C:\\Users\\Baku\\miniconda3\\python.exe new_pipeline/tests/test_landingai_parse.py

Output:
    new_pipeline/parsed/landingai/
    +-- Adrichem_2022.md
    +-- Adrichem_2022_chunks.md
    +-- Adrichem_2022.json
"""

import asyncio
import json
import os
import re
import sys
from pathlib import Path

# Fix Windows console encoding
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Setup paths
SCRIPT_DIR = Path(__file__).parent
PIPELINE_DIR = SCRIPT_DIR.parent
ROOT_DIR = PIPELINE_DIR.parent

sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(PIPELINE_DIR / ".env")

# Output directory — inside new_pipeline/parsed/
OUTPUT_DIR = PIPELINE_DIR / "parsed" / "landingai"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# PDF directory
PDF_DIR = PIPELINE_DIR / "OneDrive_1_5-6-2026"

# How many PDFs to test (set to None for all)
MAX_PDFS = 3

# Regex to strip anchor tags for clean text
ANCHOR_RE = re.compile(r"<a\s+id=['\"].*?['\"]>\s*</a>")


async def parse_with_landingai(pdf_path: Path) -> dict:
    """Parse a single PDF via LandingAI Parse Jobs API."""
    import httpx

    api_key = os.getenv("LANDINGAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("LANDINGAI_API_KEY not set")

    headers = {"Authorization": f"Bearer {api_key}"}
    base_url = "https://api.va.landing.ai/v1/ade/parse/jobs"

    # Check JSON cache first
    cache_path = OUTPUT_DIR / f"{pdf_path.stem}.json"
    if cache_path.exists():
        print(f"  [CACHE] Loading from cache: {cache_path.name}")
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    print(f"  [UPLOAD] Uploading to LandingAI...")
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Create async job
        with open(pdf_path, "rb") as f:
            files = {"document": (pdf_path.name, f, "application/pdf")}
            response = await client.post(base_url, files=files, headers=headers)

        if response.status_code not in (200, 201, 202):
            raise RuntimeError(f"API error {response.status_code}: {response.text[:300]}")

        job_data = response.json()
        job_id = job_data.get("job_id")
        if not job_id:
            raise RuntimeError(f"No job_id: {job_data}")

        print(f"  [WAIT] Job {job_id} -- polling...")

        # Poll for completion
        poll_count = 0
        while True:
            status_resp = await client.get(f"{base_url}/{job_id}", headers=headers)
            status_data = status_resp.json()
            status = status_data.get("status", "unknown")
            poll_count += 1
            print(f"     Poll #{poll_count}: {status}")

            if status == "completed":
                break
            elif status in ("failed", "error"):
                raise RuntimeError(f"Job failed: {status_data}")
            await asyncio.sleep(5)

        # Extract full result — handle both nested and flat structures
        if "chunks" in status_data:
            result = status_data
        elif "data" in status_data and "chunks" in status_data.get("data", {}):
            result = status_data["data"]
        else:
            result = status_data

    # Save FULL API response (chunks + markdown + grounding + splits + metadata)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  [SAVED] {cache_path.name}")

    return result


def clean_text(markdown: str) -> str:
    """Strip anchor tags from chunk markdown for clean text."""
    return ANCHOR_RE.sub("", markdown).strip()


def save_as_markdown(pdf_path: Path, result: dict):
    """Save parse result as readable .md files for inspection."""
    chunks = result.get("chunks", [])
    markdown = result.get("markdown", "")
    metadata = result.get("metadata", {})

    # Count by type
    type_counts = {}
    for c in chunks:
        t = c.get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    # ----- File 1: Full document markdown -----
    md_path = OUTPUT_DIR / f"{pdf_path.stem}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# {pdf_path.name}\n\n")
        f.write(f"**Pages:** {metadata.get('page_count', '?')}\n")
        f.write(f"**Total chunks:** {len(chunks)}\n")
        f.write(f"**Parse time:** {metadata.get('duration_ms', '?')}ms\n")
        f.write(f"**Model:** {metadata.get('version', '?')}\n\n")
        f.write("| Type | Count |\n|------|-------|\n")
        for t, n in sorted(type_counts.items()):
            f.write(f"| {t} | {n} |\n")
        f.write(f"\n---\n\n")
        # Write clean markdown (strip anchor tags for readability)
        if markdown:
            f.write(clean_text(markdown))
        else:
            f.write("*(no full markdown returned)*\n")
    print(f"  [MD] {md_path.name}")

    # ----- File 2: Chunk-by-chunk with metadata -----
    chunks_path = OUTPUT_DIR / f"{pdf_path.stem}_chunks.md"
    with open(chunks_path, "w", encoding="utf-8") as f:
        f.write(f"# {pdf_path.name} -- Chunk Details\n\n")

        # Summary table
        f.write(f"| # | Type | Page | Len | ID (first 8) |\n")
        f.write(f"|---|------|------|-----|---------------|\n")
        for i, c in enumerate(chunks):
            cid = c.get("id", "")[:8]
            ctype = c.get("type", "?")
            page = c.get("grounding", {}).get("page", "?")
            text = clean_text(c.get("markdown", ""))
            f.write(f"| {i+1} | {ctype} | {page} | {len(text)} | {cid} |\n")

        f.write("\n---\n\n")

        # Full chunks
        for i, chunk in enumerate(chunks):
            ctype = chunk.get("type", "unknown")
            cid = chunk.get("id", "")
            page = chunk.get("grounding", {}).get("page", "?")
            bbox = chunk.get("grounding", {}).get("box")
            text = clean_text(chunk.get("markdown", ""))

            f.write(f"### Chunk {i+1} -- `{ctype}` (page {page})\n\n")
            f.write(f"*ID: {cid}*\n\n")
            if bbox:
                f.write(f"*BBox: L={bbox.get('left',0):.3f} T={bbox.get('top',0):.3f} R={bbox.get('right',0):.3f} B={bbox.get('bottom',0):.3f}*\n\n")

            if ctype == "table":
                f.write("```html\n")
                f.write(text)
                f.write("\n```\n\n")
            elif ctype == "figure":
                f.write("> " + text.replace("\n", "\n> ") + "\n\n")
            elif ctype == "marginalia":
                f.write(f"_{text}_\n\n")
            else:
                f.write(text + "\n\n")

            f.write("---\n\n")

    print(f"  [MD] {chunks_path.name}")


async def main():
    print(f"PDF directory: {PDF_DIR}")
    print(f"Output directory: {OUTPUT_DIR}\n")

    if not PDF_DIR.exists():
        print(f"[ERROR] PDF directory not found: {PDF_DIR}")
        return

    pdf_files = sorted(PDF_DIR.glob("*.pdf"))[:MAX_PDFS]
    if not pdf_files:
        print("[ERROR] No PDFs found")
        return

    print(f"Testing with {len(pdf_files)} PDFs:\n")

    for pdf_path in pdf_files:
        print(f"{'='*60}")
        print(f"[PDF] {pdf_path.name} ({pdf_path.stat().st_size / 1024:.0f} KB)")
        print(f"{'='*60}")

        try:
            result = await parse_with_landingai(pdf_path)
            save_as_markdown(pdf_path, result)

            chunks = result.get("chunks", [])
            types = {}
            for c in chunks:
                t = c.get("type", "?")
                types[t] = types.get(t, 0) + 1

            print(f"  [OK] {len(chunks)} chunks: {types}")
            print(f"     Pages: {result.get('metadata', {}).get('page_count', '?')}")

        except Exception as e:
            print(f"  [ERROR] {e}")

        print()

    print(f"\n[DONE] All outputs saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
