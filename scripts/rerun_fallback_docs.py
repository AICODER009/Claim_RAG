"""Re-run ONLY docs with fallback table chunks — uses Claude since OpenAI quota is hit."""
import sys, json, os, time, re, logging
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

PARSED_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\LLamaParser")
REGISTRY_PATH = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\typization_registry.json")
OUTPUT_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\chunks_final")

api_key = os.getenv("OPENAI_API_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")

registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
chunker = MarkdownChunker(target_tokens=400, max_tokens=500, min_tokens=50)
linearizer = TableLinearizer(api_key=api_key, model="gpt-5.2", anthropic_api_key=anthropic_key)
metadata_ext = MetadataExtractor(api_key=api_key, model="gpt-5.2", anthropic_api_key=anthropic_key)

# Only re-run these 6 docs
rerun_files = [
    "N van Doorn 2024.md",
    "Package-Insert----Gamunex-C.md",
    "Roopenian DC, et al. .md",
    "Schroeder HW Jr, Cavacini L. J Allergy Clin Immunol. 2010.md",
    "Ulrichts J Clin Invest 2018.md",
    "van Nes_Neurology_2011.md",
]

for fname in rerun_files:
    fpath = PARSED_DIR / fname
    if not fpath.exists():
        print(f"  SKIP: {fname}")
        continue

    stem = fpath.stem
    t0 = time.time()

    typ = registry.get(stem, {})
    rt_id = typ.get("rt_id", "PENDING")
    category = typ.get("category", "PENDING")
    ref_type_name = typ.get("reference_type_name", "Pending classification")

    raw_md = fpath.read_text(encoding="utf-8")
    clean_md = preprocess(raw_md, filename=stem)
    doc_metadata = metadata_ext.extract(clean_md, filename=stem)
    chunks = chunker.chunk(clean_md, filename=stem)

    records = []
    tables_done = 0

    for c in chunks:
        source_table_html = None
        if c.segment_type == "table":
            source_table_html = c.text
            c.text = linearizer.linearize(c.text)
            tables_done += 1

        normalized_text = normalize_unicode(c.text)
        numeric_tokens = extract_numeric_tokens(normalized_text)

        record = {
            "sent_id": f"{stem}::chunk-{c.chunk_index:04d}",
            "ref_id": stem,
            "rt_id": rt_id,
            "ref_category": category,
            "reference_type_name": ref_type_name,
            "text": normalized_text,
            "section": c.section,
            "segment_type": c.segment_type,
            "chunk_index": c.chunk_index,
            "approx_tokens": len(normalized_text) // 4,
            "numeric_tokens": [
                {"value": t.normalized_value, "context": t.context}
                for t in numeric_tokens
            ],
            "source_table_html": source_table_html,
            "vector": [],
            "doc_metadata": doc_metadata,
        }
        records.append(record)

    out_path = OUTPUT_DIR / f"{stem}.chunks.json"
    out_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    elapsed = time.time() - t0
    print(f"  {stem[:55]:55s}  chunks={len(records):3d}  tables={tables_done:2d}  {elapsed:.1f}s")

print("\nDone — 6 docs re-processed.")
