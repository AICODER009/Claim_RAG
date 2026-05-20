"""Validate ALL 86 chunk JSONs against source markdown files.

Checks:
1. JSON is valid and parseable
2. Every doc has matching source .md
3. No empty text chunks
4. All table chunks are properly linearized (no raw HTML)
5. Metadata present (title at minimum)
6. Chunk count sanity (>0)
7. Numeric tokens extracted
8. sent_id format correct
9. No fallback tables remaining
"""
import sys, json, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

OUT_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\chunks_final")
MD_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\LLamaParser")

errors = []
warnings = []
stats = {
    "files": 0, "total_chunks": 0, "text_chunks": 0, "table_chunks": 0,
    "ref_chunks": 0, "figure_chunks": 0, "with_doi": 0, "with_year": 0,
    "with_trial_id": 0, "with_title": 0, "linearized_tables": 0,
    "fallback_tables": 0, "empty_text": 0, "total_numerics": 0,
}

for jf in sorted(OUT_DIR.glob("*.chunks.json")):
    stem = jf.stem.replace(".chunks", "")
    stats["files"] += 1

    # 1. JSON valid?
    try:
        data = json.loads(jf.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"INVALID JSON: {stem}: {e}")
        continue

    # 2. Source .md exists?
    md_path = MD_DIR / f"{stem}.md"
    if not md_path.exists():
        warnings.append(f"NO SOURCE MD: {stem}")

    # 3. Chunk count
    if len(data) == 0:
        errors.append(f"ZERO CHUNKS: {stem}")
        continue

    stats["total_chunks"] += len(data)

    for r in data:
        seg = r.get("segment_type", "unknown")
        if seg == "text": stats["text_chunks"] += 1
        elif seg == "table": stats["table_chunks"] += 1
        elif seg == "reference": stats["ref_chunks"] += 1
        elif seg == "figure": stats["figure_chunks"] += 1

        # 4. Empty text?
        text = r.get("text", "")
        if not text or not text.strip():
            stats["empty_text"] += 1
            errors.append(f"EMPTY TEXT: {stem}::chunk-{r.get('chunk_index', '?')}")

        # 5. Table linearization check
        if seg == "table":
            has_html = bool(re.search(r"</?t[dhrab]", text, re.IGNORECASE))
            has_sentences = "." in text and len(text) > 30
            if has_html:
                stats["fallback_tables"] += 1
                errors.append(f"RAW HTML TABLE: {stem}::chunk-{r.get('chunk_index', '?')}")
            elif not has_sentences and len(text.split()) > 3:
                stats["fallback_tables"] += 1
                warnings.append(f"STRIPPED TABLE: {stem}::chunk-{r.get('chunk_index', '?')}: {text[:60]}...")
            else:
                stats["linearized_tables"] += 1

        # 6. sent_id format
        sid = r.get("sent_id", "")
        if "::" not in sid:
            errors.append(f"BAD SENT_ID: {stem}: {sid}")

        # 7. Numeric tokens
        stats["total_numerics"] += len(r.get("numeric_tokens", []))

    # 8. Metadata
    meta = data[0].get("doc_metadata", {})
    if meta.get("title"):
        stats["with_title"] += 1
    else:
        warnings.append(f"NO TITLE: {stem}")
    if meta.get("doi"): stats["with_doi"] += 1
    if meta.get("year"): stats["with_year"] += 1
    if meta.get("trial_id"): stats["with_trial_id"] += 1

# Print results
print("=" * 70)
print("CORPUS VALIDATION REPORT")
print("=" * 70)

print(f"\nFiles: {stats['files']}/86")
print(f"Total chunks: {stats['total_chunks']}")
print(f"  text:      {stats['text_chunks']}")
print(f"  table:     {stats['table_chunks']}  (linearized: {stats['linearized_tables']}, fallback: {stats['fallback_tables']})")
print(f"  reference: {stats['ref_chunks']}")
print(f"  figure:    {stats['figure_chunks']}")
print(f"Empty text:  {stats['empty_text']}")
print(f"Total numerics extracted: {stats['total_numerics']}")

print(f"\nMetadata coverage:")
print(f"  with title:    {stats['with_title']}/{stats['files']}")
print(f"  with year:     {stats['with_year']}/{stats['files']}")
print(f"  with DOI:      {stats['with_doi']}/{stats['files']}")
print(f"  with trial_id: {stats['with_trial_id']}/{stats['files']}")

if errors:
    print(f"\nERRORS ({len(errors)}):")
    for e in errors[:20]:
        print(f"  {e}")
    if len(errors) > 20:
        print(f"  ...and {len(errors) - 20} more")
else:
    print("\nERRORS: 0")

if warnings:
    print(f"\nWARNINGS ({len(warnings)}):")
    for w in warnings[:20]:
        print(f"  {w}")
    if len(warnings) > 20:
        print(f"  ...and {len(warnings) - 20} more")
else:
    print("\nWARNINGS: 0")

# Sample 3 random docs — show their metadata for manual verification
print(f"\n{'=' * 70}")
print("SAMPLE RECORDS FOR MANUAL CHECK")
print("=" * 70)
import random
random.seed(42)
samples = random.sample(list(OUT_DIR.glob("*.chunks.json")), 3)
for sf in samples:
    data = json.loads(sf.read_text(encoding="utf-8"))
    meta = data[0].get("doc_metadata", {})
    tables = [r for r in data if r["segment_type"] == "table"]
    print(f"\n  {sf.stem}")
    print(f"    chunks: {len(data)}, tables: {len(tables)}")
    print(f"    title: {meta.get('title', 'NONE')[:70]}")
    print(f"    year: {meta.get('year', 'NONE')}, doi: {meta.get('doi', 'NONE')[:40]}")
    if tables:
        print(f"    sample table text: {tables[0]['text'][:120]}...")

print(f"\nOutput directory: {OUT_DIR}")
print(f"Total size: {sum(f.stat().st_size for f in OUT_DIR.glob('*.chunks.json')) / 1024 / 1024:.1f} MB")
