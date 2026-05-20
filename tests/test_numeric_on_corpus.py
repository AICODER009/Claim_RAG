"""Test numeric extraction on REAL corpus .md files to verify citation filtering.

Tests 5 different document types to catch edge cases:
- Journal article with heavy citations (Hughes 2001)
- Lancet article with tables + stats (Allen 2024)
- Conference poster (Hargraves AAN 2025)
- PI with dosing numbers (VYVGART)
- Cochrane review with forest plot stats (Hughes 2017)
"""

import sys, os, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\revisto_evidence_aligned_clean")

from pathlib import Path
from new_pipeline.ingestion.normalizer import normalize_unicode, extract_numeric_tokens
from new_pipeline.ingestion.preprocessor import preprocess

PARSED_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\LLamaParser")

TEST_FILES = [
    "Hughes R 2001_Ann Neurol.md",           # Heavy superscript citations
    "Allen_Lancet Neuro_2024.md",            # Stats-dense journal article
    "Hargraves AAN 2025.md",                 # Conference poster
    "vyvgart-hytrulo-prescribing-information_3.26.md",  # PI with doses
    "Hughes_Cochrane Database Syst Rev_2017.md",  # Systematic review
]

for fname in TEST_FILES:
    fpath = PARSED_DIR / fname
    if not fpath.exists():
        print(f"\nSKIP: {fname}")
        continue

    raw = fpath.read_text(encoding="utf-8")
    clean = preprocess(raw, filename=fname)
    normalized = normalize_unicode(clean)

    # Extract from first 5000 chars (representative sample)
    sample = normalized[:5000]
    tokens = extract_numeric_tokens(sample)

    print(f"\n{'='*70}")
    print(f"FILE: {fname}")
    print(f"  Sample: first 5000 chars | Found: {len(tokens)} numeric tokens")
    print(f"  {'─'*66}")

    for t in tokens[:15]:  # show first 15
        ctx_short = t.context.replace('\n', ' ')[:65]
        print(f"  {t.raw_value:18s}  ctx: ...{ctx_short}...")

    if len(tokens) > 15:
        print(f"  ... and {len(tokens) - 15} more tokens")

    # Check for suspicious leaks: bare single digits 1-9 without clinical context
    suspicious = [t for t in tokens if t.raw_value.isdigit() and int(t.raw_value) < 10]
    if suspicious:
        print(f"\n  ⚠ SUSPICIOUS bare digits (possible citation leaks):")
        for t in suspicious:
            ctx_short = t.context.replace('\n', ' ')[:65]
            print(f"    {t.raw_value:5s}  ctx: {ctx_short}")

print(f"\n{'='*70}")

# Now show a FINAL chunk JSON with full context-augmented numerics
print("\n\n" + "=" * 70)
print("FINAL CHUNK JSON FORMAT (with context-augmented numeric tokens)")
print("=" * 70)

# Use a real chunk from Allen 2024
sample_text = normalize_unicode(
    "[Articles > Results]\n"
    "In stage B, CIDP relapse or clinical worsening occurred in 12 (21%) "
    "of 57 participants in the efgartigimod group and 26 (46%) of 57 in "
    "the placebo group (HR 0.39, 95% CI 0.19-0.77; p=0.006)."
)
tokens = extract_numeric_tokens(sample_text)

# Build the chunk record as it will look in the JSON
chunk_record = {
    "sent_id": "Allen_Lancet Neuro_2024::chunk-0035",
    "ref_id": "Allen_Lancet Neuro_2024",
    "rt_id": "RT-301",
    "ref_category": "B3",
    "reference_type_name": "Peer-reviewed full-text journal article",
    "text": sample_text,
    "section": "Articles > Results",
    "segment_type": "text",
    "chunk_index": 35,
    "approx_tokens": len(sample_text.split()) * 4 // 3,
    "numeric_tokens": [
        {
            "value": t.normalized_value,
            "context": t.context,
        }
        for t in tokens
    ],
    "vector": [0.0234, -0.1456, "...768 floats total..."],
    "doc_metadata": {
        "authors": "Allen JA, Vu T, Abuzinadah AR, et al.",
        "title": "Safety, tolerability, and efficacy of SC efgartigimod in CIDP",
        "journal": "Lancet Neurology",
        "year": 2024,
        "doi": "10.1016/S1474-4422(24)00250-1"
    }
}

print(json.dumps(chunk_record, indent=2, ensure_ascii=False))
