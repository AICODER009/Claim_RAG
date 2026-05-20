"""Test the full pre-process → chunk pipeline on a LlamaParser file."""

import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\revisto_evidence_aligned_clean")

from pathlib import Path
from new_pipeline.ingestion.preprocessor import preprocess
from new_pipeline.ingestion.chunker import MarkdownChunker

PARSED_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\LLamaParser")

# Test on the document with known fake tables
test_files = [
    "Al-zuhairy 2021.md",    # 9 tables (4 real + 5 fake)
    "Allen_Lancet Neuro_2024.md",  # clinical trial
]

chunker = MarkdownChunker()

for fname in test_files:
    fpath = PARSED_DIR / fname
    if not fpath.exists():
        print(f"SKIP: {fname} not found")
        continue

    md = fpath.read_text(encoding="utf-8")
    print(f"\n{'='*70}")
    print(f"FILE: {fname}")
    print(f"  Raw: {len(md)} chars")

    # Pre-process
    cleaned = preprocess(md, filename=fname)
    print(f"  After preprocess: {len(cleaned)} chars (removed {len(md) - len(cleaned)})")

    # Chunk
    chunks = chunker.chunk(cleaned, filename=fpath.stem)

    # Stats
    type_counts = {}
    token_buckets = {"<100": 0, "100-300": 0, "300-500": 0, "500+": 0}
    for c in chunks:
        type_counts[c.segment_type] = type_counts.get(c.segment_type, 0) + 1
        t = c.approx_tokens
        if t < 100: token_buckets["<100"] += 1
        elif t < 300: token_buckets["100-300"] += 1
        elif t < 500: token_buckets["300-500"] += 1
        else: token_buckets["500+"] += 1

    print(f"  Total chunks: {len(chunks)}")
    print(f"  By type: {type_counts}")
    print(f"  Token distribution: {token_buckets}")
    print(f"  Avg tokens: {sum(c.approx_tokens for c in chunks) // max(len(chunks), 1)}")

    # Show first 5 chunks
    print(f"\n  --- First 5 chunks ---")
    for c in chunks[:5]:
        preview = c.text[:120].replace("\n", " ")
        print(f"  [{c.chunk_index}] {c.segment_type:10s} ~{c.approx_tokens:3d}tok  section='{c.section[:50]}...' ")
        print(f"       {preview}...")

    # Show a table chunk if any
    table_chunks = [c for c in chunks if c.segment_type == "table"]
    if table_chunks:
        print(f"\n  --- First table chunk ---")
        tc = table_chunks[0]
        preview = tc.text[:200].replace("\n", " ")
        print(f"  [{tc.chunk_index}] section='{tc.section}' ~{tc.approx_tokens}tok")
        print(f"       {preview}...")

    # Show any oversized chunks (>500 tokens)
    oversized = [c for c in chunks if c.approx_tokens > 500]
    if oversized:
        print(f"\n  WARNING: {len(oversized)} chunks exceed 500 tokens!")
        for c in oversized:
            print(f"    [{c.chunk_index}] {c.segment_type} ~{c.approx_tokens}tok section='{c.section[:40]}'")

print("\nDONE")
