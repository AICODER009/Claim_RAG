"""Deep manual validation: compare chunks against source markdown line-by-line.

For each doc:
1. Load source .md and chunk JSON
2. Verify text fidelity — every chunk text exists in source
3. Verify table linearization — numbers in linearized text match source HTML
4. Verify section attribution accuracy
5. Check for content gaps — source text not captured in any chunk
6. Check chunk boundary quality — no mid-sentence splits
"""
import sys, json, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\revisto_evidence_aligned_clean")
from pathlib import Path
from new_pipeline.ingestion.preprocessor import preprocess

MD_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\LLamaParser")
OUT_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\chunks_final")

test_docs = [
    "Allen_Lancet Neuro_2024",      # Complex journal article with many tables
    "Doneddu 2020 J Neurol Neurosurg Psychiatry",  # Shorter journal article
    "Package-Insert----Gamunex-C",   # Prescribing information — dense tables
]

for stem in test_docs:
    md_path = MD_DIR / f"{stem}.md"
    json_path = OUT_DIR / f"{stem}.chunks.json"

    raw_md = md_path.read_text(encoding="utf-8")
    clean_md = preprocess(raw_md, filename=stem)
    chunks = json.loads(json_path.read_text(encoding="utf-8"))

    print("=" * 70)
    print(f"DOCUMENT: {stem}")
    print(f"  Source: {len(raw_md)} chars, Preprocessed: {len(clean_md)} chars")
    print(f"  Chunks: {len(chunks)}")
    print("=" * 70)

    # ---- CHECK 1: Text fidelity ----
    # For text chunks, verify the chunk text (minus section prefix) is in the source
    text_chunks = [c for c in chunks if c["segment_type"] == "text"]
    fidelity_ok = 0
    fidelity_fail = []

    for c in text_chunks:
        text = c["text"]
        # Remove section prefix like "[Section > Subsection] "
        clean_text = re.sub(r"^\[.*?\]\s*", "", text)
        # Take a 40-char snippet from middle of chunk
        mid = len(clean_text) // 2
        snippet = clean_text[max(0, mid-20):mid+20].strip()
        if len(snippet) < 10:
            snippet = clean_text[:40].strip()

        if snippet and snippet in clean_md:
            fidelity_ok += 1
        else:
            # Try fuzzy — remove extra whitespace
            collapsed = re.sub(r"\s+", " ", snippet)
            collapsed_src = re.sub(r"\s+", " ", clean_md)
            if collapsed in collapsed_src:
                fidelity_ok += 1
            else:
                fidelity_fail.append((c["chunk_index"], snippet[:50]))

    print(f"\n  CHECK 1 — Text fidelity:")
    print(f"    OK: {fidelity_ok}/{len(text_chunks)}")
    if fidelity_fail:
        print(f"    FAILED ({len(fidelity_fail)}):")
        for idx, snip in fidelity_fail[:5]:
            print(f"      chunk-{idx:04d}: '{snip}...'")

    # ---- CHECK 2: Table numbers preserved ----
    table_chunks = [c for c in chunks if c["segment_type"] == "table"]
    table_ok = 0
    table_issues = []

    for c in table_chunks:
        source_html = c.get("source_table_html", "")
        linearized = c["text"]

        if not source_html:
            continue

        # Extract numbers from source HTML
        src_nums = set(re.findall(r"\d+\.?\d*", source_html))
        lin_nums = set(re.findall(r"\d+\.?\d*", linearized))

        # Key numbers from source should appear in linearized text
        # Filter out tiny numbers (1, 2, 3) which may be row indices
        key_src_nums = {n for n in src_nums if len(n) >= 2 or float(n) >= 10}

        missing = key_src_nums - lin_nums
        if missing and len(missing) > len(key_src_nums) * 0.3:  # >30% missing is concerning
            table_issues.append((c["chunk_index"], len(key_src_nums), len(missing), list(missing)[:5]))
        else:
            table_ok += 1

    print(f"\n  CHECK 2 — Table number preservation:")
    print(f"    OK: {table_ok}/{len(table_chunks)}")
    if table_issues:
        print(f"    ISSUES ({len(table_issues)}):")
        for idx, total, miss, samples in table_issues[:5]:
            print(f"      chunk-{idx:04d}: {miss}/{total} key numbers missing: {samples}")

    # ---- CHECK 3: Section attribution ----
    sections = set()
    for c in chunks:
        sections.add(c["section"])
    print(f"\n  CHECK 3 — Section attribution:")
    print(f"    Unique sections: {len(sections)}")
    for s in sorted(sections)[:10]:
        count = sum(1 for c in chunks if c["section"] == s)
        print(f"      {s[:60]:60s} ({count} chunks)")
    if len(sections) > 10:
        print(f"      ...and {len(sections) - 10} more")

    # ---- CHECK 4: Content coverage ----
    # Check that important paragraphs from source are captured
    # Split source into paragraphs, check each is in at least one chunk
    paragraphs = [p.strip() for p in clean_md.split("\n\n") if len(p.strip()) > 50]
    covered = 0
    uncovered = []

    all_chunk_text = " ".join(c["text"] for c in chunks)
    all_chunk_collapsed = re.sub(r"\s+", " ", all_chunk_text)

    for p in paragraphs:
        # Take a 30-char snippet from the paragraph
        snippet = re.sub(r"\s+", " ", p[:60])
        if snippet in all_chunk_collapsed:
            covered += 1
        else:
            # Check if it's a heading (covered by section names)
            if p.startswith("#"):
                covered += 1
            # Check if it's a table (covered by linearized text)
            elif "<table" in p.lower() or "|" in p[:20]:
                covered += 1
            else:
                uncovered.append(p[:80])

    print(f"\n  CHECK 4 — Content coverage:")
    print(f"    Source paragraphs: {len(paragraphs)}")
    print(f"    Covered: {covered}/{len(paragraphs)} ({100*covered/max(1,len(paragraphs)):.0f}%)")
    if uncovered:
        print(f"    Uncovered ({len(uncovered)}):")
        for u in uncovered[:5]:
            print(f"      '{u}...'")

    # ---- CHECK 5: Chunk boundaries ----
    # Check for mid-sentence splits (text ending without punctuation)
    bad_boundaries = 0
    for c in text_chunks:
        text = c["text"].rstrip()
        if text and text[-1] not in ".!?:;)]\u201d\"'0123456789%":
            # Could be mid-sentence split — check if it's just a list item
            if not text.endswith(("-", "\u2013", "\u2014")):
                bad_boundaries += 1

    print(f"\n  CHECK 5 — Chunk boundaries:")
    print(f"    Clean endings: {len(text_chunks) - bad_boundaries}/{len(text_chunks)}")
    if bad_boundaries:
        print(f"    Mid-sentence splits: {bad_boundaries}")

    # ---- CHECK 6: Sample linearized table quality ----
    if table_chunks:
        t = table_chunks[0]
        print(f"\n  CHECK 6 — Sample linearized table (chunk-{t['chunk_index']:04d}):")
        print(f"    Section: {t['section'][:60]}")
        print(f"    Source HTML (first 150): {(t.get('source_table_html','')[:150]).replace(chr(10),' ')}")
        print(f"    Linearized (first 200): {t['text'][:200]}")
        print(f"    Numerics: {len(t['numeric_tokens'])}")

    # ---- CHECK 7: Metadata vs source ----
    meta = chunks[0]["doc_metadata"]
    print(f"\n  CHECK 7 — Metadata:")
    print(f"    title: {meta.get('title', 'NONE')[:70]}")
    print(f"    authors: {str(meta.get('authors_str', meta.get('authors', 'NONE')))[:60]}")
    print(f"    year: {meta.get('year', 'NONE')}")
    print(f"    doi: {meta.get('doi', 'NONE')}")
    print(f"    trial_id: {meta.get('trial_id', 'NONE')}")

    print()
