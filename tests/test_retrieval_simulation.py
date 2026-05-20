"""End-to-end retrieval simulation: will claims match both text AND table chunks?

Tests:
1. Take Allen 2024 — real text chunk + real table chunk from same paper
2. Linearize the table
3. Run normalizer on both
4. Simulate claim matching (semantic overlap check)
5. Show the final single-pass output format
"""
import sys, json, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\revisto_evidence_aligned_clean")

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\.env"))

from new_pipeline.ingestion.content_cleaner import TableLinearizer
from new_pipeline.ingestion.normalizer import normalize_unicode, extract_numeric_tokens
from new_pipeline.ingestion.preprocessor import preprocess
from new_pipeline.ingestion.chunker import MarkdownChunker

api_key = os.getenv("OPENAI_API_KEY")

# ---------------------------------------------------------------
# Step 1: Chunk Allen 2024
# ---------------------------------------------------------------
PARSED_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\LLamaParser")
fpath = PARSED_DIR / "Allen_Lancet Neuro_2024.md"
raw = fpath.read_text(encoding="utf-8")
clean = preprocess(raw, filename=fpath.stem)
chunker = MarkdownChunker(target_tokens=400, max_tokens=500, min_tokens=50)
chunks = chunker.chunk(clean, filename=fpath.stem)

# Find a results text chunk and a table chunk
text_chunks = [c for c in chunks if c.segment_type == "text" and "result" in c.section.lower()]
table_chunks = [c for c in chunks if c.segment_type == "table"]

# Pick one with "relapse" data
result_chunk = None
for c in text_chunks:
    if "relapse" in c.text.lower() and "21%" in c.text:
        result_chunk = c
        break

table_chunk = table_chunks[2] if len(table_chunks) > 2 else table_chunks[0]

print("=" * 70)
print("SCENARIO: Claim references data from Allen 2024")
print("=" * 70)

# ---------------------------------------------------------------
# Step 2: Show the raw text chunk
# ---------------------------------------------------------------
print("\n--- TEXT CHUNK (as-is, ready for embedding) ---")
text_for_embed = normalize_unicode(result_chunk.text) if result_chunk else "(no relapse chunk found)"
print(f"  section: {result_chunk.section[:60] if result_chunk else 'N/A'}")
print(f"  segment_type: text")
print(f"  text: {text_for_embed[:300]}...")

text_nums = extract_numeric_tokens(text_for_embed) if result_chunk else []
print(f"  numeric_tokens ({len(text_nums)}):")
for t in text_nums[:5]:
    print(f"    {t.normalized_value:10s} | {t.context[:55]}")

# ---------------------------------------------------------------
# Step 3: Linearize the table
# ---------------------------------------------------------------
print("\n--- TABLE CHUNK (BEFORE linearization — raw HTML) ---")
raw_table = table_chunk.text
print(f"  section: {table_chunk.section[:60]}")
print(f"  segment_type: table")
print(f"  raw HTML (first 150 chars): {raw_table.replace(chr(10), ' ')[:150]}...")
print(f"  tokens: {table_chunk.approx_tokens}")

linearizer = TableLinearizer(api_key=api_key, model="gpt-4o-mini")
linearized = linearizer.linearize(raw_table)

print("\n--- TABLE CHUNK (AFTER linearization — natural language) ---")
linearized_norm = normalize_unicode(linearized)
print(f"  text: {linearized_norm[:400]}...")

table_nums = extract_numeric_tokens(linearized_norm)
print(f"  numeric_tokens ({len(table_nums)}):")
for t in table_nums[:5]:
    print(f"    {t.normalized_value:10s} | {t.context[:55]}")

# ---------------------------------------------------------------
# Step 4: Simulate claim matching
# ---------------------------------------------------------------
print("\n" + "=" * 70)
print("CLAIM MATCHING SIMULATION")
print("=" * 70)

claims = [
    "Efgartigimod reduced CIDP relapse by 21%",
    "The hazard ratio for relapse was 0.39",
    "629 patients were assessed for eligibility",
]

for claim in claims:
    print(f"\n  CLAIM: \"{claim}\"")

    # Check which chunks have overlapping numbers
    claim_nums = extract_numeric_tokens(claim)
    claim_values = {t.normalized_value for t in claim_nums}

    text_values = {t.normalized_value for t in text_nums}
    table_values = {t.normalized_value for t in table_nums}

    text_overlap = claim_values & text_values
    table_overlap = claim_values & table_values

    print(f"    Claim numbers: {claim_values}")
    print(f"    Text chunk match:  {text_overlap or 'NONE'}")
    print(f"    Table chunk match: {table_overlap or 'NONE'}")

    if text_overlap:
        print(f"    -> TEXT chunk from same paper WILL be retrieved (shared: {text_overlap})")
    if table_overlap:
        print(f"    -> TABLE chunk from same paper WILL be retrieved (shared: {table_overlap})")
    if not text_overlap and not table_overlap:
        print(f"    -> Neither chunk has this number — search relies on semantic similarity only")

# ---------------------------------------------------------------
# Step 5: Show FINAL single-pass output format
# ---------------------------------------------------------------
print("\n" + "=" * 70)
print("FINAL SINGLE-PASS OUTPUT FORMAT")
print("=" * 70)

# Text chunk record
text_record = {
    "sent_id": f"Allen_Lancet Neuro_2024::chunk-{result_chunk.chunk_index:04d}",
    "ref_id": "Allen_Lancet Neuro_2024",
    "rt_id": "RT-301",
    "ref_category": "B3",
    "reference_type_name": "Peer-reviewed full-text journal article",
    "text": text_for_embed[:200] + "...",
    "section": result_chunk.section,
    "segment_type": "text",
    "chunk_index": result_chunk.chunk_index,
    "approx_tokens": len(text_for_embed) // 4,
    "numeric_tokens": [
        {"value": t.normalized_value, "context": t.context[:60]}
        for t in text_nums[:4]
    ],
    "vector": ["<768 floats from MedCPT Article Encoder>"],
    "doc_metadata": {
        "title": "Efgartigimod in CIDP (ADHERE): phase 2 trial",
        "authors_str": "Allen JA, Vu T et al.",
        "year": 2024,
        "doi": "10.1016/S1474-4422(24)00250-1",
        "trial_id": "NCT04281472",
    },
}

# Table chunk record (AFTER linearization)
table_record = {
    "sent_id": f"Allen_Lancet Neuro_2024::chunk-{table_chunk.chunk_index:04d}",
    "ref_id": "Allen_Lancet Neuro_2024",
    "rt_id": "RT-301",
    "ref_category": "B3",
    "reference_type_name": "Peer-reviewed full-text journal article",
    "text": linearized_norm[:200] + "...",
    "section": table_chunk.section,
    "segment_type": "table",
    "chunk_index": table_chunk.chunk_index,
    "approx_tokens": len(linearized_norm) // 4,
    "source_table_html": raw_table[:100] + "...(preserved for audit)",
    "numeric_tokens": [
        {"value": t.normalized_value, "context": t.context[:60]}
        for t in table_nums[:4]
    ],
    "vector": ["<768 floats from MedCPT Article Encoder>"],
    "doc_metadata": {
        "title": "Efgartigimod in CIDP (ADHERE): phase 2 trial",
        "authors_str": "Allen JA, Vu T et al.",
        "year": 2024,
        "doi": "10.1016/S1474-4422(24)00250-1",
        "trial_id": "NCT04281472",
    },
}

print("\n--- TEXT CHUNK RECORD ---")
print(json.dumps(text_record, indent=2, ensure_ascii=False))

print("\n--- TABLE CHUNK RECORD (linearized) ---")
print(json.dumps(table_record, indent=2, ensure_ascii=False))
