"""Compare the 23 patched files vs 63 re-run files for structural alignment."""
import sys, json, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime

OUT_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\chunks_final")

# The terminated run started around 10:58 UTC and ran until ~11:40 UTC
# Files written by the terminated run will have mtime in that window
# Files NOT written will have earlier mtime (from run 1/2) + local patch

files_rerun = []  # Written by the terminated full run
files_patched = []  # Only patched locally

for jf in sorted(OUT_DIR.glob("*.chunks.json")):
    mtime = jf.stat().st_mtime
    dt = datetime.fromtimestamp(mtime)
    data = json.loads(jf.read_text(encoding="utf-8"))

    # Check a sample chunk's fields
    sample = data[0]
    fields = sorted(sample.keys())

    info = {
        "stem": jf.stem[:45],
        "mtime": dt.strftime("%H:%M:%S"),
        "chunks": len(data),
        "fields": fields,
        "has_embeddable": "embeddable" in sample,
        "meta_keys": sorted(sample.get("doc_metadata", {}).keys()),
    }

    # The re-run happened between ~10:58 and ~11:40 UTC on May 9
    # Files written in that window were re-run; others were patched
    if dt.hour >= 10 and dt.hour <= 11 and dt.minute >= 58:
        files_rerun.append(info)
    elif dt.hour == 11:
        files_rerun.append(info)
    else:
        files_patched.append(info)

print(f"Files from re-run: {len(files_rerun)}")
print(f"Files from patch-only: {len(files_patched)}")

# Compare field sets
if files_rerun and files_patched:
    rerun_fields = set(tuple(f["fields"]) for f in files_rerun)
    patch_fields = set(tuple(f["fields"]) for f in files_patched)

    print(f"\nRe-run field schema (unique): {len(rerun_fields)}")
    for fs in rerun_fields:
        print(f"  {list(fs)}")

    print(f"\nPatch-only field schema (unique): {len(patch_fields)}")
    for fs in patch_fields:
        print(f"  {list(fs)}")

    if rerun_fields == patch_fields:
        print("\n>>> SCHEMAS MATCH — all files have identical field structure")
    else:
        diff = rerun_fields.symmetric_difference(patch_fields)
        print(f"\n>>> SCHEMA MISMATCH!")
        print(f"  Differences: {diff}")

    # Compare metadata keys
    rerun_meta = set(tuple(f["meta_keys"]) for f in files_rerun)
    patch_meta = set(tuple(f["meta_keys"]) for f in files_patched)
    print(f"\nRe-run metadata schemas: {len(rerun_meta)}")
    for m in rerun_meta:
        print(f"  {list(m)}")
    print(f"Patch metadata schemas: {len(patch_meta)}")
    for m in patch_meta:
        print(f"  {list(m)}")

# Check specific alignment issues
print("\n\n--- DETAILED COMPARISON ---")
print("Picking 1 re-run file and 1 patched file, showing chunk[0]:\n")

if files_rerun:
    r = files_rerun[0]
    jf = OUT_DIR / (r["stem"].strip() + ".chunks.json")
    if not jf.exists():
        for f in OUT_DIR.glob("*.chunks.json"):
            if f.stem.startswith(r["stem"].strip()[:20]):
                jf = f
                break
    data = json.loads(jf.read_text(encoding="utf-8"))
    c = data[0]
    print(f"RE-RUN FILE: {jf.stem[:50]}")
    for k in sorted(c.keys()):
        v = c[k]
        if isinstance(v, str) and len(v) > 60:
            v = v[:60] + "..."
        elif isinstance(v, list) and len(v) > 3:
            v = f"[{len(v)} items]"
        elif isinstance(v, dict):
            v = f"{{keys: {sorted(v.keys())}}}"
        print(f"  {k:25s}: {v}")

if files_patched:
    p = files_patched[0]
    jf = OUT_DIR / (p["stem"].strip() + ".chunks.json")
    if not jf.exists():
        for f in OUT_DIR.glob("*.chunks.json"):
            if f.stem.startswith(p["stem"].strip()[:20]):
                jf = f
                break
    data = json.loads(jf.read_text(encoding="utf-8"))
    c = data[0]
    print(f"\nPATCHED FILE: {jf.stem[:50]}")
    for k in sorted(c.keys()):
        v = c[k]
        if isinstance(v, str) and len(v) > 60:
            v = v[:60] + "..."
        elif isinstance(v, list) and len(v) > 3:
            v = f"[{len(v)} items]"
        elif isinstance(v, dict):
            v = f"{{keys: {sorted(v.keys())}}}"
        print(f"  {k:25s}: {v}")
