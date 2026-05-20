import sys, json, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
OUT = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\chunks_final")

# Find Al-zuhairy 2021
print("Al-Zuhairy files:")
for f in sorted(OUT.glob("*uhairy*")):
    print(f"  {f.stem}")
for f in sorted(OUT.glob("*zuhairy*")):
    print(f"  {f.stem}")

# Check the ref garbage
print("\n--- Reference chunks with journal noise ---")
for stem in ["Adrichem_2022", "Al-Zuhairy 2022"]:
    data = json.loads((OUT / f"{stem}.chunks.json").read_text(encoding="utf-8"))
    refs = [c for c in data if c["segment_type"] == "reference"]
    for c in refs:
        if re.search(r"WILEY|Downloaded|MUSCLE.*NERVE", c["text"], re.IGNORECASE):
            ci = c["chunk_index"]
            txt = c["text"][:120]
            print(f"  [{stem}] chunk-{ci:04d}: {txt}...")

# Check footnote stitching gap
print("\n--- Footnote stitching gap example ---")
data = json.loads((OUT / "Al-Zuhairy 2022.chunks.json").read_text(encoding="utf-8"))
for c in data:
    if c["segment_type"] == "table" and "<sup>" in c.get("source_table_html", ""):
        print(f"  Table chunk-{c['chunk_index']:04d}:")
        # Find sup markers in source
        sups = re.findall(r"<sup>([a-c])</sup>", c.get("source_table_html", ""))
        print(f"    Source has footnote markers: {sups}")
        # Check if linearized text has the p-value
        has_pval = bool(re.search(r"[Pp]\s*[=<]\s*0?\.\d+", c["text"]))
        print(f"    Linearized text has p-value: {has_pval}")
        print(f"    Linearized: {c['text'][:150]}...")
        break
