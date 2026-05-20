"""Sample: preprocess + chunk + merge typization → JSON output.

This shows the EXACT format that goes into the embedding step.
Each chunk has ALL the metadata needed for downstream retrieval + audit.
"""

import sys, os, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\revisto_evidence_aligned_clean")

from pathlib import Path
from new_pipeline.ingestion.preprocessor import preprocess
from new_pipeline.ingestion.chunker import MarkdownChunker

PARSED_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\LLamaParser")
REGISTRY_PATH = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\typization_registry.json")
OUTPUT_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\chunks")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load typization registry
registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

# Process 3 different document types as samples
SAMPLES = [
    "Allen_Lancet Neuro_2024.md",         # B3 journal article (long, many tables)
    "Hargraves AAN 2025.md",              # B4 conference poster (short)
    "vyvgart-hytrulo-prescribing-information_3.26.md",  # B1 PI (structured)
]

chunker = MarkdownChunker(target_tokens=400, max_tokens=500, min_tokens=50)

for fname in SAMPLES:
    fpath = PARSED_DIR / fname
    if not fpath.exists():
        print(f"SKIP: {fname}")
        continue

    stem = fpath.stem
    typ = registry.get(stem, {})
    rt_id = typ.get("rt_id", "UNKNOWN")
    category = typ.get("category", "UNKNOWN")
    ref_type_name = typ.get("reference_type_name", "UNKNOWN")

    # Step 1: preprocess
    raw_md = fpath.read_text(encoding="utf-8")
    clean_md = preprocess(raw_md, filename=stem)

    # Step 2: chunk
    chunks = chunker.chunk(clean_md, filename=stem)

    # Step 3: build output records — this is what goes to embedding/Qdrant
    records = []
    for c in chunks:
        record = {
            # Identity
            "sent_id": f"{stem}::chunk-{c.chunk_index:04d}",
            "ref_id": stem,

            # From typization (per-document, same for all chunks)
            "rt_id": rt_id,
            "ref_category": category,
            "reference_type_name": ref_type_name,

            # From chunker (per-chunk)
            "text": c.text,
            "section": c.section,
            "segment_type": c.segment_type,
            "heading_level": c.heading_level,
            "chunk_index": c.chunk_index,
            "approx_tokens": c.approx_tokens,

            # Placeholders — filled by later pipeline steps
            "numeric_tokens": [],   # Step 6: normalizer
            "vector": [],           # Step 7: MedCPT embed
            "doc_metadata": {},     # Step 3: metadata extraction
        }
        records.append(record)

    # Save per-document chunk file
    out_path = OUTPUT_DIR / f"{stem}.chunks.json"
    out_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")

    # Print summary
    print(f"\n{'='*70}")
    print(f"FILE: {fname}")
    print(f"  Type: {rt_id} ({category}) — {ref_type_name}")
    print(f"  Raw: {len(raw_md)} chars | Clean: {len(clean_md)} chars")
    print(f"  Chunks: {len(records)}")

    # Distribution
    type_counts = {}
    for r in records:
        t = r["segment_type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    print(f"  By type: {type_counts}")

    # Token stats
    tokens = [r["approx_tokens"] for r in records]
    print(f"  Tokens: min={min(tokens)}, max={max(tokens)}, avg={sum(tokens)//len(tokens)}")

    # Show first 3 chunks
    print(f"\n  --- Sample chunks ---")
    for r in records[:3]:
        text_preview = r["text"][:120].replace("\n", " ")
        print(f"  [{r['chunk_index']:3d}] {r['segment_type']:10s} ~{r['approx_tokens']:3d}tok  "
              f"section='{r['section'][:50]}...'")
        print(f"       {text_preview}...")

    # Show a table chunk if any
    for r in records:
        if r["segment_type"] == "table":
            text_preview = r["text"][:120].replace("\n", " ")
            print(f"\n  --- Table chunk example ---")
            print(f"  [{r['chunk_index']:3d}] ~{r['approx_tokens']}tok  section='{r['section'][:50]}'")
            print(f"       {text_preview}...")
            break

    print(f"\n  Saved: {out_path}")

print(f"\n{'='*70}")
print("DONE — chunk JSONs saved to parsed/chunks/")
print(f"{'='*70}")
