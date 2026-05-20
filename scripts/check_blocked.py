#!/usr/bin/env python3
"""Check if BLOCKED claims actually exist in source evidence documents."""
import os, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

claims = [
    ("2", "not inject.*into a vein or muscle", "You should not inject VYVGART HYTRULO into a vein or muscle."),
    ("3", "if it is expired", "Do not use VYVGART HYTRULO if it is expired."),
    ("5", "novel treatment", "A novel treatment for adult patients with CIDP"),
    ("7", "Do not share.*prefilled syringe", "Do not share the prefilled syringe."),
    ("10", "Do not freeze", "Do not freeze VYVGART HYTRULO."),
    ("11", "room temperature.*longer than 30", "Do not use if at room temp >30 days"),
    ("15", "20 to 30 seconds", "For subcutaneous injection over 20 to 30 seconds"),
    ("17", "86.*F.*30.*C|30.*C.*86", "Stored at room temp up to 86°F (30°C)"),
    ("21", "Discard.*unused portion", "Discard any unused portion"),
    ("22", "check the expiration date", "First, patients need to check the expiration date"),
    ("33", "warm.*any other way", "Do not attempt to warm prefilled syringe in any other way"),
    ("34", "warm.*any other way", "Do not attempt to warm filled syringe in any other way"),
    ("36", "room temperature.*longer than 30 days", "Do not use if at room temp >30 days"),
    ("41", "wash.*hands", "Patients should wash hands with soap and water"),
    ("50", "Do not inject into a vein", "Do not inject into a vein."),
]

# Search directories
search_dirs = []
for d in [
    Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\LLamaParser"),
    Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\chunks_final"),
    Path(r"D:\revisto_evidence_aligned_clean\agentic_substantiation_package\reference_corpus_mds"),
]:
    if d.exists():
        search_dirs.append(d)

print(f"Searching in: {[str(d) for d in search_dirs]}\n")

all_files = []
for d in search_dirs:
    for f in d.rglob("*"):
        if f.suffix in [".md", ".txt", ".json"] and f.stat().st_size < 5_000_000:
            all_files.append(f)

print(f"Total files to search: {len(all_files)}\n")
print("=" * 70)

found_count = 0
not_found_count = 0

for claim_id, pattern, description in claims:
    found_in = []
    regex = re.compile(pattern, re.IGNORECASE)
    for f in all_files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
            matches = regex.findall(text)
            if matches:
                found_in.append((f.name, matches[0][:60]))
        except:
            pass

    if found_in:
        found_count += 1
        print(f"  #{claim_id}: ✅ FOUND in {len(found_in)} file(s) — {description[:60]}")
        for fn, match in found_in[:3]:
            print(f"       -> {fn}: \"{match}\"")
    else:
        not_found_count += 1
        print(f"  #{claim_id}: ❌ NOT FOUND — {description[:60]}")

print("\n" + "=" * 70)
print(f"FOUND in sources: {found_count}/15 — should have been PASS (retrieval gap)")
print(f"NOT in sources:   {not_found_count}/15 — correctly BLOCKED (no evidence exists)")
