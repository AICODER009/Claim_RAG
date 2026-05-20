"""Check ALL requirements from the parser quality analysis against actual chunks.

Requirements from the detailed LlamaParse assessment:
1. Claim sentence integrity (no mid-word hyphenation)
2. In-text citation markers attached to claims
3. Reference list as discrete entries
4. Footnote marker linkage (sup tags)
5. Stats preserved inline with claims
6. Page furniture stripped
7. OCR fidelity (Guillain-Barre etc.)
8. Fabricated table filter applied
9. No page-break garbage in references
10. Footnote stitching (p-values with superscript markers)
"""
import sys, json, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

OUT_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\chunks_final")
MD_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\LLamaParser")

# Load test docs from the original assessment
test_docs = {
    "Adrichem_2022": None,
    "Al-zuhairy 2021 (1)": None,  
    "Al-Zuhairy 2022": None,
}

for stem in list(test_docs.keys()):
    jf = OUT_DIR / f"{stem}.chunks.json"
    if jf.exists():
        test_docs[stem] = json.loads(jf.read_text(encoding="utf-8"))
    else:
        # Try case variants
        for f in OUT_DIR.glob("*.chunks.json"):
            if stem.lower().replace(" ", "").replace("-","") in f.stem.lower().replace(" ","").replace("-",""):
                test_docs[stem] = json.loads(f.read_text(encoding="utf-8"))
                break

print("=" * 70)
print("PARSER REQUIREMENT COMPLIANCE CHECK")
print("=" * 70)

for stem, chunks in test_docs.items():
    if not chunks:
        print(f"\n  SKIP: {stem} — file not found")
        continue

    print(f"\n{'='*60}")
    print(f"DOCUMENT: {stem}")
    print(f"  Total chunks: {len(chunks)}")
    print(f"{'='*60}")

    text_chunks = [c for c in chunks if c["segment_type"] == "text"]
    table_chunks = [c for c in chunks if c["segment_type"] == "table"]
    ref_chunks = [c for c in chunks if c["segment_type"] == "reference"]
    all_text = " ".join(c["text"] for c in chunks)

    # REQ 1: No hyphenation artifacts (calcu-lated, demyelina-tion)
    hyphen_pattern = re.compile(r"[a-z]- [a-z]")
    hyphen_hits = hyphen_pattern.findall(all_text)
    print(f"\n  [REQ 1] Hyphenation artifacts: {len(hyphen_hits)}")
    if hyphen_hits:
        for h in hyphen_hits[:3]:
            idx = all_text.index(h)
            print(f"    '{all_text[max(0,idx-10):idx+15]}'")
    print(f"  STATUS: {'PASS' if len(hyphen_hits) == 0 else 'WARN'}")

    # REQ 2: Citation markers preserved (<sup> tags)
    sup_count = len(re.findall(r"<sup>", all_text, re.IGNORECASE))
    print(f"\n  [REQ 2] Citation markers (<sup>): {sup_count}")
    print(f"  STATUS: {'PASS' if sup_count > 0 or 'zuhairy' not in stem.lower() else 'WARN'}")

    # REQ 3: References as discrete entries
    print(f"\n  [REQ 3] Reference entries: {len(ref_chunks)}")
    # Check that each ref chunk looks like a single entry
    multi_ref = sum(1 for c in ref_chunks if re.search(r"\d+\.\s+[A-Z].*\d+\.\s+[A-Z]", c["text"]))
    print(f"    Multi-entry ref chunks: {multi_ref} (should be 0)")
    if ref_chunks:
        print(f"    Sample: {ref_chunks[0]['text'][:80]}...")
    print(f"  STATUS: {'PASS' if multi_ref == 0 else 'WARN'}")

    # REQ 4: Footnote markers present
    footnote_markers = re.findall(r"<sup>[a-c]</sup>", all_text, re.IGNORECASE)
    print(f"\n  [REQ 4] Footnote markers (<sup>a</sup> etc.): {len(footnote_markers)}")
    # Check if footnote definitions exist
    footnote_defs = re.findall(r"<sup>[a-c]</sup>\s*[):]?\s*[Pp]\s*[=<]", all_text)
    print(f"    Footnote definitions (p-value): {len(footnote_defs)}")
    print(f"  STATUS: INFO (footnotes present if doc has them)")

    # REQ 5: Stats inline with claims
    stats_patterns = [
        (r"95%\s*CI", "95% CI"),
        (r"p\s*[<>=]\s*0\.\d+", "p-value"),
        (r"HR\s+\d+\.\d+", "hazard ratio"),
        (r"OR\s+\d+\.\d+", "odds ratio"),
    ]
    print(f"\n  [REQ 5] Stats preserved inline:")
    for pattern, label in stats_patterns:
        count = len(re.findall(pattern, all_text, re.IGNORECASE))
        if count:
            print(f"    {label}: {count} occurrences")

    # REQ 6: Page furniture stripped
    page_furniture = re.findall(r"<page_(header|footer)>", all_text)
    downloaded = len(re.findall(r"Downloaded from", all_text, re.IGNORECASE))
    print(f"\n  [REQ 6] Page furniture:")
    print(f"    <page_header/footer> tags remaining: {len(page_furniture)}")
    print(f"    'Downloaded from' noise: {downloaded}")
    print(f"  STATUS: {'PASS' if not page_furniture else 'FAIL'}")

    # REQ 7: OCR fidelity
    barre_clean = len(re.findall(r"Barr[eé]", all_text))
    barre_corrupt = len(re.findall(r"Barr\[", all_text))
    control_chars = len(re.findall(r"[\x00-\x1f]", all_text.replace("\n", "").replace("\t", "")))
    print(f"\n  [REQ 7] OCR fidelity:")
    print(f"    'Barre/Barré' clean: {barre_clean}")
    print(f"    Corrupt Barre: {barre_corrupt}")
    print(f"    Control chars: {control_chars}")
    print(f"  STATUS: {'PASS' if barre_corrupt == 0 and control_chars == 0 else 'WARN'}")

    # REQ 8: Fabricated tables filtered
    # Check if any table has "Patient 1", "Patient 2" fabricated labels
    fabricated = [c for c in table_chunks if re.search(r"Patient\s+\d+", c.get("source_table_html", ""))]
    print(f"\n  [REQ 8] Fabricated tables:")
    print(f"    Table chunks: {len(table_chunks)}")
    print(f"    With 'Patient N' labels: {len(fabricated)}")
    print(f"  STATUS: {'PASS' if len(fabricated) == 0 else 'FAIL'}")

    # REQ 9: Reference integrity (no page-break garbage)
    broken_refs = [c for c in ref_chunks if re.search(r"WILEY|Downloaded|MUSCLE.*NERVE", c["text"], re.IGNORECASE)]
    print(f"\n  [REQ 9] Reference integrity:")
    print(f"    Refs with page-break garbage: {len(broken_refs)}")
    print(f"  STATUS: {'PASS' if len(broken_refs) == 0 else 'WARN'}")

    # REQ 10: embeddable flag correct
    emb_refs = [c for c in ref_chunks if c.get("embeddable") == True]
    print(f"\n  [REQ 10] Reference exclusion from search:")
    print(f"    Ref chunks with embeddable=True: {len(emb_refs)} (should be 0)")
    print(f"  STATUS: {'PASS' if len(emb_refs) == 0 else 'FAIL'}")

# Final summary
print(f"\n\n{'='*70}")
print("KEY FINDINGS vs ORIGINAL ASSESSMENT")
print("="*70)
print("""
The parser quality analysis identified 10 requirements.

IMPLEMENTED in our pipeline:
  [1] Page furniture stripped         - preprocessor.strip_page_furniture()
  [2] Fabricated table filter         - preprocessor.filter_fake_tables()
  [3] Section-aware chunking          - chunker uses heading hierarchy
  [4] Tables split by row-groups      - chunker._split_table_if_needed()
  [5] References as discrete entries  - chunker._split_reference_block()
  [6] Citation markers preserved      - <sup> tags pass through
  [7] Stats inline                    - chunker keeps paragraphs whole
  [8] embeddable flag                 - refs excluded from vector search
  [9] Sentence overlap at boundaries  - chunker uses overlap_sent

NOT YET IMPLEMENTED (identified gaps):
  [A] Footnote stitching              - NOT DONE. Superscript a/b/c in table
                                        cells are not appended with their 
                                        footnote definition text. This means
                                        a retrieval on 'p = 0.2' won't find
                                        the cell value it qualifies.
  [B] Dehyphenation pass              - NOT NEEDED (LlamaParse doesn't produce 
                                        hyphen splits, that was Landing AI only)
""")
