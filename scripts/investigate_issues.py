"""Investigate the 7 'critical' issues — are they real blockers or false alarms?"""
import sys, json, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

OUT_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\chunks_final")
MD_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\LLamaParser")

# ISSUE 1: Control chars in 3 chunks
print("=" * 60)
print("ISSUE 1: CONTROL CHARACTERS")
print("=" * 60)
ctrl_files = [
    ("ARGX-113-1902 - ADHERE+ Clinical Study Protocol Version 8 - 02 Jul 2024", [137, 319]),
    ("Package-Insert----Gamunex-C", [87]),
]
for stem, idxs in ctrl_files:
    data = json.loads((OUT_DIR / f"{stem}.chunks.json").read_text(encoding="utf-8"))
    for idx in idxs:
        c = data[idx]
        text = c["text"]
        ctrl_chars = [(i, hex(ord(ch))) for i, ch in enumerate(text) if ord(ch) < 32 and ch not in "\n\t\r"]
        print(f"\n  {stem}::chunk-{idx}")
        for pos, h in ctrl_chars:
            context = text[max(0,pos-20):pos+20]
            print(f"    Position {pos}: {h} in context: '...{repr(context)}...'")
        print(f"    Embeddable: {c['embeddable']}")
        print(f"    Segment: {c['segment_type']}")

# ISSUE 2: Low coverage docs — what's being missed?
print(f"\n{'='*60}")
print("ISSUE 2: LOW COVERAGE DOCUMENTS")
print("=" * 60)
low_cov_docs = [
    "AANEM Collegium 2025 CIDP Show File_ GS Section",
    "Allen JA AAN 2025",
    "Hargraves AAN 2025",
    "Saint Luke_s Health System_Understanding Therapeutic Plasma Exchange (TPE) _webpage",
]
for stem in low_cov_docs:
    md_path = MD_DIR / f"{stem}.md"
    if not md_path.exists():
        candidates = list(MD_DIR.glob(f"{stem[:30]}*"))
        if candidates:
            md_path = candidates[0]
        else:
            print(f"\n  {stem}: SOURCE NOT FOUND")
            continue

    raw_md = md_path.read_text(encoding="utf-8")
    data = json.loads((OUT_DIR / f"{stem}.chunks.json").read_text(encoding="utf-8"))
    all_chunk_text = re.sub(r"\s+", " ", " ".join(c["text"] for c in data))

    paragraphs = [p.strip() for p in raw_md.split("\n\n") if len(p.strip()) > 60]
    missed = []
    for p in paragraphs:
        snippet = re.sub(r"\s+", " ", p[:60])
        if snippet not in all_chunk_text and not p.startswith("#") and "<table" not in p.lower() and "<page_" not in p.lower():
            missed.append(p[:80])

    print(f"\n  {stem[:50]}:")
    print(f"    Total paragraphs: {len(paragraphs)}, Missed: {len(missed)}")
    print(f"    Doc type: rt_id={data[0]['rt_id']}, cat={data[0]['ref_category']}")
    for m in missed[:3]:
        print(f"    MISSED: '{m}...'")
