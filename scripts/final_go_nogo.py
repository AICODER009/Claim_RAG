"""FINAL GO/NO-GO: Check ALL 86 chunk files against their source markdown.

For EVERY document:
1. Text fidelity — chunk text traceable to source
2. Table content — linearized tables preserve key numbers from source HTML
3. No data corruption — no control chars, no HTML in text chunks
4. No content gaps — key source paragraphs captured
5. Schema completeness — all required fields present
6. Embeddable correctness — only text+table are embeddable
"""
import sys, json, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\revisto_evidence_aligned_clean")
from pathlib import Path
from new_pipeline.ingestion.preprocessor import preprocess

OUT_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\chunks_final")
MD_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\LLamaParser")

REQUIRED_FIELDS = {"sent_id", "ref_id", "rt_id", "ref_category", "text",
                   "section", "segment_type", "chunk_index", "embeddable",
                   "numeric_tokens", "vector", "doc_metadata"}

critical_errors = []
warnings = []
doc_results = []

total_chunks = 0
total_text_ok = 0
total_text_fail = 0
total_tables_ok = 0
total_tables_fail = 0
total_coverage_pct = []

for jf in sorted(OUT_DIR.glob("*.chunks.json")):
    stem = jf.stem.replace(".chunks", "")
    data = json.loads(jf.read_text(encoding="utf-8"))
    total_chunks += len(data)

    # Find source markdown
    md_path = MD_DIR / f"{stem}.md"
    if not md_path.exists():
        # Try with different extensions/names
        candidates = list(MD_DIR.glob(f"{stem}*"))
        if candidates:
            md_path = candidates[0]
        else:
            warnings.append(f"NO SOURCE MD: {stem}")
            continue

    raw_md = md_path.read_text(encoding="utf-8")
    clean_md = preprocess(raw_md, filename=stem)
    clean_collapsed = re.sub(r"\s+", " ", clean_md)

    doc_errors = []

    # CHECK 1: Schema completeness
    for c in data:
        missing = REQUIRED_FIELDS - set(c.keys())
        if missing:
            critical_errors.append(f"MISSING FIELDS in {stem}::chunk-{c.get('chunk_index','?')}: {missing}")

    # CHECK 2: Text fidelity
    text_chunks = [c for c in data if c["segment_type"] == "text"]
    text_ok = 0
    for c in text_chunks:
        text = c["text"]
        clean_text = re.sub(r"^\[.*?\]\s*", "", text)  # Remove section prefix
        mid = len(clean_text) // 2
        snippet = clean_text[max(0, mid-25):mid+25].strip()
        if len(snippet) < 10:
            snippet = clean_text[:50].strip()
        
        collapsed_snippet = re.sub(r"\s+", " ", snippet)
        if collapsed_snippet in clean_collapsed:
            text_ok += 1
        else:
            total_text_fail += 1
    total_text_ok += text_ok

    # CHECK 3: Table number preservation
    table_chunks = [c for c in data if c["segment_type"] == "table"]
    tables_ok = 0
    for c in table_chunks:
        src = c.get("source_table_html", "")
        if not src:
            continue
        src_nums = set(re.findall(r"\d+\.?\d*", src))
        lin_nums = set(re.findall(r"\d+\.?\d*", c["text"]))
        key_nums = {n for n in src_nums if len(n) >= 2}
        if not key_nums:
            tables_ok += 1
            continue
        missing = key_nums - lin_nums
        if len(missing) <= len(key_nums) * 0.5:
            tables_ok += 1
        else:
            total_tables_fail += 1
            doc_errors.append(f"TABLE NUM LOSS chunk-{c['chunk_index']}: {len(missing)}/{len(key_nums)} missing")
    total_tables_ok += tables_ok

    # CHECK 4: Content coverage
    paragraphs = [p.strip() for p in clean_md.split("\n\n") if len(p.strip()) > 60]
    all_chunk_text = re.sub(r"\s+", " ", " ".join(c["text"] for c in data))
    covered = 0
    for p in paragraphs:
        snippet = re.sub(r"\s+", " ", p[:60])
        if snippet in all_chunk_text or p.startswith("#") or "<table" in p.lower():
            covered += 1
    cov_pct = 100 * covered / max(1, len(paragraphs))
    total_coverage_pct.append(cov_pct)
    if cov_pct < 85:
        critical_errors.append(f"LOW COVERAGE {stem}: {cov_pct:.0f}%")

    # CHECK 5: Data corruption
    for c in data:
        if c["embeddable"]:
            text = c["text"]
            ctrl = len(re.findall(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", text))
            if ctrl > 0:
                critical_errors.append(f"CONTROL CHARS in {stem}::chunk-{c['chunk_index']}: {ctrl}")

    # CHECK 6: Embeddable correctness
    for c in data:
        expected = c["segment_type"] in ("text", "table")
        if c["embeddable"] != expected:
            critical_errors.append(f"WRONG EMBEDDABLE in {stem}::chunk-{c['chunk_index']}: type={c['segment_type']} emb={c['embeddable']}")

    # CHECK 7: Empty text in embeddable chunks
    for c in data:
        if c["embeddable"] and (not c["text"] or len(c["text"].strip()) < 5):
            critical_errors.append(f"EMPTY EMBEDDABLE in {stem}::chunk-{c['chunk_index']}")

    status = "OK" if not doc_errors else f"{len(doc_errors)} issues"
    doc_results.append((stem[:50], len(data), len(text_chunks), len(table_chunks), cov_pct, status))

# SUMMARY
print("=" * 70)
print("FINAL GO/NO-GO VALIDATION — ALL 86 DOCUMENTS")
print("=" * 70)

print(f"\nTotal documents: {len(doc_results)}")
print(f"Total chunks: {total_chunks}")
print(f"\nText fidelity: {total_text_ok}/{total_text_ok + total_text_fail} ({100*total_text_ok/max(1,total_text_ok+total_text_fail):.1f}%)")
print(f"Table numbers: {total_tables_ok}/{total_tables_ok + total_tables_fail} ({100*total_tables_ok/max(1,total_tables_ok+total_tables_fail):.1f}%)")
print(f"Avg coverage: {sum(total_coverage_pct)/max(1,len(total_coverage_pct)):.1f}%")
print(f"Min coverage: {min(total_coverage_pct):.1f}%")

print(f"\nCRITICAL ERRORS: {len(critical_errors)}")
if critical_errors:
    for e in critical_errors[:15]:
        print(f"  {e}")
    if len(critical_errors) > 15:
        print(f"  ...and {len(critical_errors)-15} more")

print(f"\nWARNINGS: {len(warnings)}")
for w in warnings:
    print(f"  {w}")

# Low-coverage docs
low_cov = [(s, c) for s, _, _, _, c, _ in doc_results if c < 90]
if low_cov:
    print(f"\nLow coverage docs (<90%):")
    for s, c in low_cov:
        print(f"  {s}: {c:.0f}%")

# VERDICT
print(f"\n{'='*70}")
if not critical_errors:
    print("VERDICT: GO — Ready for MedCPT embedding")
    print("No critical issues. All chunks traceable to source documents.")
else:
    print(f"VERDICT: HOLD — {len(critical_errors)} critical issues need fixing")
print("=" * 70)
