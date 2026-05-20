"""Find docs with fallback (non-linearized) table chunks and re-run only those."""
import sys, json, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

OUT_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\chunks_final")

needs_rerun = []
ok_count = 0

for f in sorted(OUT_DIR.glob("*.chunks.json")):
    data = json.loads(f.read_text(encoding="utf-8"))
    tables = [r for r in data if r["segment_type"] == "table"]
    if not tables:
        ok_count += 1
        continue

    # Check if tables are properly linearized (no HTML tags) or fallback (stripped HTML)
    bad_tables = 0
    for t in tables:
        text = t["text"]
        # Fallback tables: either have HTML tags or are just whitespace-collapsed cell values
        # Properly linearized: natural language sentences with periods
        has_html = bool(re.search(r"</?t[dhrab]", text, re.IGNORECASE))
        has_sentences = "." in text and len(text) > 30
        # Fallback strip produces text like "Header1 Header2 Val1 Val2" — no periods, no sentence structure
        looks_stripped = not has_sentences and not has_html and len(text.split()) > 3

        if has_html or looks_stripped:
            bad_tables += 1

    if bad_tables > 0:
        needs_rerun.append((f.stem, len(tables), bad_tables))
    else:
        ok_count += 1

print(f"OK (properly linearized): {ok_count}")
print(f"Need re-run: {len(needs_rerun)}")
print()
for stem, total, bad in needs_rerun:
    print(f"  {stem[:55]:55s}  tables={total:2d}  bad={bad:2d}")
