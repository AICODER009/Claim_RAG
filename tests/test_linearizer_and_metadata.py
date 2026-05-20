"""Test table linearizer and metadata extractor on real corpus data."""
import sys, json, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\revisto_evidence_aligned_clean")

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\.env"))

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("ERROR: No OPENAI_API_KEY in .env")
    sys.exit(1)

# ---------------------------------------------------------------
# TEST 1: Table Linearizer
# ---------------------------------------------------------------
print("=" * 70)
print("TEST 1: Table Linearizer")
print("=" * 70)

from new_pipeline.ingestion.content_cleaner import TableLinearizer

linearizer = TableLinearizer(api_key=api_key, model="gpt-4o-mini")

# Get a real table from a chunked file
chunks_dir = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\chunks")
test_file = chunks_dir / "Allen_Lancet Neuro_2024.chunks.json"
chunks = json.loads(test_file.read_text(encoding="utf-8"))

table_chunks = [c for c in chunks if c["segment_type"] == "table"]
print(f"Found {len(table_chunks)} table chunks in Allen 2024")
print()

# Test on first 2 tables
for i, tc in enumerate(table_chunks[:2]):
    raw_html = tc["text"][:500]
    print(f"--- Table {i+1} (original, first 500 chars) ---")
    print(raw_html.replace("\n", " ")[:200])
    print()

    result = linearizer.linearize(tc["text"])
    print(f"--- Table {i+1} (linearized) ---")
    print(result[:500])
    print()

print(f"Linearizer stats: {linearizer.stats}")

# ---------------------------------------------------------------
# TEST 2: Metadata Extractor (regex-only first, then GPT)
# ---------------------------------------------------------------
print()
print("=" * 70)
print("TEST 2: Metadata Extractor")
print("=" * 70)

from new_pipeline.ingestion.metadata_extractor import MetadataExtractor
from new_pipeline.ingestion.preprocessor import preprocess

PARSED_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\LLamaParser")

extractor = MetadataExtractor(api_key=api_key, model="gpt-4o-mini")

# Test on 4 diverse docs
test_docs = [
    "Allen_Lancet Neuro_2024.md",       # Journal article
    "Hargraves AAN 2025.md",            # Conference poster
    "vyvgart-hytrulo-prescribing-information_3.26.md",  # PI
    "Argenx BVBA.md",                   # CSR
]

for fname in test_docs:
    fpath = PARSED_DIR / fname
    if not fpath.exists():
        print(f"SKIP: {fname}")
        continue
    raw = fpath.read_text(encoding="utf-8")
    clean = preprocess(raw, filename=fpath.stem)

    # Regex-only first
    regex_meta = extractor.extract_without_llm(clean, filename=fpath.stem)
    print(f"\n--- {fname[:50]} ---")
    print(f"  REGEX: {json.dumps(regex_meta, indent=None, ensure_ascii=False)[:200]}")

    # GPT extraction
    gpt_meta = extractor.extract(clean, max_words=400)
    print(f"  GPT:   {json.dumps(gpt_meta, indent=None, ensure_ascii=False)[:200]}")

print(f"\nExtractor stats: {extractor.stats}")
