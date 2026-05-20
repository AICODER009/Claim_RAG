"""Check if all 86 files have properly linearized tables after the interrupted run."""
import sys, json, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime

OUT_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\chunks_final")

ok_count = 0
bad_files = []

for jf in sorted(OUT_DIR.glob("*.chunks.json")):
    mtime = datetime.fromtimestamp(jf.stat().st_mtime)
    data = json.loads(jf.read_text(encoding="utf-8"))
    tables = [r for r in data if r["segment_type"] == "table"]

    bad = 0
    for t in tables:
        text = t["text"]
        has_html = bool(re.search(r"</?t[dhrab]", text, re.IGNORECASE))
        has_sentences = "." in text and len(text) > 30
        looks_stripped = not has_sentences and not has_html and len(text.split()) > 3
        if has_html or looks_stripped:
            bad += 1

    if bad > 0:
        bad_files.append((jf.stem[:50], len(tables), bad, mtime.strftime("%Y-%m-%d %H:%M")))
    else:
        ok_count += 1

print(f"Files with ALL tables properly linearized: {ok_count}/86")
print(f"Files with fallback tables: {len(bad_files)}")

if bad_files:
    print("\nPROBLEM FILES:")
    for stem, total, bad, t in bad_files:
        print(f"  {stem:50s}  tables={total:2d}  bad={bad:2d}  last_modified={t}")
else:
    print("\nAll tables properly linearized. No issues.")

# Also check: did the interrupted run produce any partial/corrupt JSONs?
print("\n--- JSON INTEGRITY CHECK ---")
corrupt = 0
for jf in sorted(OUT_DIR.glob("*.chunks.json")):
    try:
        data = json.loads(jf.read_text(encoding="utf-8"))
        if not isinstance(data, list) or len(data) == 0:
            print(f"  EMPTY: {jf.stem}")
            corrupt += 1
        # Check that all required fields exist
        for c in data:
            for field in ["sent_id", "ref_id", "rt_id", "text", "segment_type", "embeddable"]:
                if field not in c:
                    print(f"  MISSING FIELD '{field}': {jf.stem}::chunk-{c.get('chunk_index','?')}")
                    corrupt += 1
                    break
    except json.JSONDecodeError:
        print(f"  CORRUPT JSON: {jf.stem}")
        corrupt += 1

if corrupt == 0:
    print("  All 86 files valid, complete, and have all required fields.")
else:
    print(f"  {corrupt} issues found!")
