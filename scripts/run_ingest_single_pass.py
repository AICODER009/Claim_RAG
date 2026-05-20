"""Single-pass ingestion orchestrator — preprocess, chunk, linearize, normalize, metadata, save.

All transformations happen in memory. JSON is saved ONCE at the end.
No index drift, no multi-pass inconsistency.
"""
import sys, json, os, time, logging
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\revisto_evidence_aligned_clean")

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\.env"))

from new_pipeline.ingestion.preprocessor import preprocess
from new_pipeline.ingestion.chunker import MarkdownChunker
from new_pipeline.ingestion.content_cleaner import TableLinearizer
from new_pipeline.ingestion.normalizer import normalize_unicode, extract_numeric_tokens
from new_pipeline.ingestion.metadata_extractor import MetadataExtractor

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("ingest")
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------
# Config
# ---------------------------------------------------------------
PARSED_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\LLamaParser")
REGISTRY_PATH = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\typization_registry.json")
OUTPUT_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\chunks_final")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

api_key = os.getenv("OPENAI_API_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    print("ERROR: No OPENAI_API_KEY in .env")
    sys.exit(1)
if not anthropic_key:
    print("WARNING: No ANTHROPIC_API_KEY — no Claude fallback on quota errors")

# ---------------------------------------------------------------
# Initialize modules
# ---------------------------------------------------------------
registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
chunker = MarkdownChunker(target_tokens=400, max_tokens=500, min_tokens=50)
linearizer = TableLinearizer(api_key=api_key, model="gpt-5.2", anthropic_api_key=anthropic_key)
metadata_ext = MetadataExtractor(api_key=api_key, model="gpt-5.2", anthropic_api_key=anthropic_key)

# ---------------------------------------------------------------
# Select files: sample or all
# ---------------------------------------------------------------
SAMPLE_MODE = False  # Full corpus with embeddable flag

if SAMPLE_MODE:
    sample_files = [
        "Allen_Lancet Neuro_2024.md",          # Journal article (many tables)
        "Hargraves AAN 2025.md",               # Conference poster
        "vyvgart-hytrulo-prescribing-information_3.26.md",  # PI
    ]
    all_files = [PARSED_DIR / f for f in sample_files if (PARSED_DIR / f).exists()]
    print(f"SAMPLE MODE: {len(all_files)} files")
else:
    all_files = sorted(PARSED_DIR.glob("*.md"))
    print(f"FULL MODE: {len(all_files)} files")

# ---------------------------------------------------------------
# Single-pass pipeline
# ---------------------------------------------------------------
total_chunks = 0
total_tables_linearized = 0
total_time = 0
errors = []

for fpath in all_files:
    stem = fpath.stem
    t0 = time.time()
    try:
        # --- Lookup typization (graceful for new docs not yet classified) ---
        typ = registry.get(stem, {})
        rt_id = typ.get("rt_id", "PENDING")
        category = typ.get("category", "PENDING")
        ref_type_name = typ.get("reference_type_name", "Pending classification")
        if not typ:
            logger.warning(f"'{stem}' not in typization registry — marking as PENDING")

        # --- Step 1: Preprocess ---
        raw_md = fpath.read_text(encoding="utf-8")
        clean_md = preprocess(raw_md, filename=stem)

        # --- Step 3: Extract metadata (regex deep-scan + GPT) ---
        doc_metadata = metadata_ext.extract(clean_md, filename=stem)

        # --- Step 4: Chunk ---
        chunks = chunker.chunk(clean_md, filename=stem)

        # --- Build records with all transformations ---
        records = []
        tables_in_doc = 0

        for c in chunks:
            source_table_html = None

            # --- Step 5: Linearize tables ---
            if c.segment_type == "table":
                source_table_html = c.text  # Preserve raw HTML for audit
                c.text = linearizer.linearize(c.text)
                tables_in_doc += 1
                total_tables_linearized += 1

            # --- Step 6: Normalize + extract numerics ---
            normalized_text = normalize_unicode(c.text)

            # Determine embeddability — reference & figure chunks excluded
            # from vector search to prevent:
            # - Secondary reference pollution (cited paper titles containing clinical data)
            # - Page range/volume numbers matching clinical claims
            # - Figure caption noise
            is_embeddable = c.segment_type in ("text", "table")

            # Only extract numeric tokens for embeddable chunks
            # Reference numbers (page ranges, volumes, DOIs) are not clinical data
            if is_embeddable:
                numeric_tokens = extract_numeric_tokens(normalized_text)
            else:
                numeric_tokens = []

            record = {
                # Identity
                "sent_id": f"{stem}::chunk-{c.chunk_index:04d}",
                "ref_id": stem,

                # Typization (per-document)
                "rt_id": rt_id,
                "ref_category": category,
                "reference_type_name": ref_type_name,

                # Content (per-chunk)
                "text": normalized_text,
                "section": c.section,
                "segment_type": c.segment_type,
                "chunk_index": c.chunk_index,
                "approx_tokens": len(normalized_text) // 4,

                # Retrieval control
                "embeddable": is_embeddable,

                # Numeric provenance (only for embeddable chunks)
                "numeric_tokens": [
                    {"value": t.normalized_value, "context": t.context}
                    for t in numeric_tokens
                ],

                # Audit trail for tables
                "source_table_html": source_table_html,

                # Placeholder for embedding
                "vector": [],

                # Bibliographic metadata (same for all chunks from this doc)
                "doc_metadata": doc_metadata,
            }
            records.append(record)

        # --- Save ---
        out_path = OUTPUT_DIR / f"{stem}.chunks.json"
        out_path.write_text(
            json.dumps(records, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        elapsed = time.time() - t0
        total_time += elapsed
        total_chunks += len(records)

        print(
            f"  {stem[:55]:55s}  "
            f"chunks={len(records):3d}  "
            f"tables={tables_in_doc:2d}  "
            f"meta={bool(doc_metadata.get('title')):1}  "
            f"{elapsed:.1f}s  "
            f"rt={rt_id}"
        )

    except Exception as e:
        errors.append((stem, str(e)))
        print(f"  ERROR: {stem}: {e}")
        import traceback; traceback.print_exc()

# ---------------------------------------------------------------
# Summary
# ---------------------------------------------------------------
print(f"\n{'='*70}")
print(f"DONE: {len(all_files)} files -> {total_chunks} chunks")
print(f"Tables linearized: {total_tables_linearized}")
print(f"Linearizer stats: {linearizer.stats}")
print(f"Metadata stats: {metadata_ext.stats}")
print(f"Total time: {total_time:.1f}s")
print(f"Output: {OUTPUT_DIR}")
if errors:
    print(f"\nERRORS ({len(errors)}):")
    for name, err in errors:
        print(f"  {name}: {err}")
else:
    print("No errors.")
print(f"{'='*70}")
