"""Run chunking on ALL 86 documents and save as JSON with typization metadata.

Output: parsed/chunks/<stem>.chunks.json for each document.
Each chunk record has all metadata needed for downstream processing.
"""
import sys, json, logging
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\revisto_evidence_aligned_clean")

from pathlib import Path
from new_pipeline.ingestion.preprocessor import preprocess
from new_pipeline.ingestion.chunker import MarkdownChunker
from new_pipeline.ingestion.normalizer import (
    normalize_unicode, extract_numeric_tokens
)

logging.basicConfig(level=logging.WARNING)

PARSED_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\LLamaParser")
REGISTRY_PATH = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\typization_registry.json")
OUTPUT_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\chunks")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load typization registry
registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

chunker = MarkdownChunker(target_tokens=400, max_tokens=500, min_tokens=50)
all_files = sorted(PARSED_DIR.glob("*.md"))

total_chunks = 0
total_tokens = 0
errors = []

for fpath in all_files:
    stem = fpath.stem
    try:
        # Typization lookup
        typ = registry.get(stem, {})
        rt_id = typ.get("rt_id", "UNKNOWN")
        category = typ.get("category", "UNKNOWN")
        ref_type_name = typ.get("reference_type_name", "UNKNOWN")

        # Step 1: Preprocess
        raw_md = fpath.read_text(encoding="utf-8")
        clean_md = preprocess(raw_md, filename=stem)

        # Step 4: Chunk
        chunks = chunker.chunk(clean_md, filename=stem)

        # Build records with all metadata
        records = []
        for c in chunks:
            # Step 6: Normalize text + extract numeric tokens with context
            normalized_text = normalize_unicode(c.text)
            numeric_tokens = extract_numeric_tokens(normalized_text)

            record = {
                # Identity
                "sent_id": f"{stem}::chunk-{c.chunk_index:04d}",
                "ref_id": stem,

                # From typization (per-document)
                "rt_id": rt_id,
                "ref_category": category,
                "reference_type_name": ref_type_name,

                # From chunker (per-chunk)
                "text": normalized_text,
                "section": c.section,
                "segment_type": c.segment_type,
                "chunk_index": c.chunk_index,
                "approx_tokens": c.approx_tokens,

                # From normalizer (per-chunk)
                "numeric_tokens": [
                    {"value": t.normalized_value, "context": t.context}
                    for t in numeric_tokens
                ],

                # Placeholders for later pipeline steps
                "vector": [],           # Step 7: MedCPT
                "doc_metadata": {},     # Step 3: metadata extraction
            }
            records.append(record)

        # Save
        out_path = OUTPUT_DIR / f"{stem}.chunks.json"
        out_path.write_text(
            json.dumps(records, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        doc_tokens = sum(r["approx_tokens"] for r in records)
        total_chunks += len(records)
        total_tokens += doc_tokens

        print(
            f"  {stem[:55]:55s}  "
            f"chunks={len(records):3d}  "
            f"avg={doc_tokens // max(len(records), 1):3d}tok  "
            f"rt={rt_id}"
        )

    except Exception as e:
        errors.append((stem, str(e)))
        print(f"  ERROR: {stem}: {e}")

print(f"\n{'='*70}")
print(f"DONE: {len(all_files)} files → {total_chunks} chunks")
print(f"Avg tokens/chunk: {total_tokens // max(total_chunks, 1)}")
print(f"Output: {OUTPUT_DIR}")
if errors:
    print(f"\nERRORS ({len(errors)}):")
    for name, err in errors:
        print(f"  {name}: {err}")
else:
    print("No errors.")
print(f"{'='*70}")
