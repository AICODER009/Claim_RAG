"""Apply manual corrections to the typization registry."""

import sys, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

reg_path = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\typization_registry.json")
reg = json.loads(reg_path.read_text(encoding="utf-8"))

fixes = []

# Fix 1: Van den Bergh 2021 — guideline, not journal article
key = "Van den Bergh_Eur J Neurol_2021"
if key in reg:
    old = reg[key]["rt_id"]
    reg[key]["rt_id"] = "RT-311"
    reg[key]["reference_type_name"] = "Specialty-society clinical practice guideline"
    reg[key]["reasoning"] = (
        "MANUAL OVERRIDE: EAN/PNS guideline for CIDP diagnosis and treatment. "
        "Published in journal but is a clinical practice guideline (RT-311), "
        "not a research article."
    )
    reg[key]["confidence"] = 1.0
    fixes.append(f"  {key}: {old} -> RT-311")

# Fix 2: CTEP — not a clinical trial
key = "CTEP Trial Development and Conduct - NCI"
if key in reg:
    old_rt = reg[key]["rt_id"]
    old_cat = reg[key]["category"]
    reg[key]["rt_id"] = "RT-311"
    reg[key]["category"] = "B3"
    reg[key]["reference_type_name"] = "Clinical trial methodology guidance (NCI)"
    reg[key]["reasoning"] = (
        "MANUAL OVERRIDE: NCI guidance document about HOW to conduct clinical "
        "trials, not a clinical trial itself. Reclassified from B2 to B3."
    )
    reg[key]["confidence"] = 1.0
    fixes.append(f"  {key}: {old_rt} ({old_cat}) -> RT-311 (B3)")

# Fix 3: Nullify meaningless 0.95 confidence
nullified = 0
for name, v in reg.items():
    if v["confidence"] == 0.95:
        v["confidence"] = None
        nullified += 1

# Save
reg_path.write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding="utf-8")

print("=== MANUAL CORRECTIONS APPLIED ===")
for f in fixes:
    print(f)
print(f"  Confidence: nullified {nullified} auto-classified docs (0.95 was meaningless)")

# Recount categories
cat_dist = {}
for v in reg.values():
    cat = v["category"]
    cat_dist[cat] = cat_dist.get(cat, 0) + 1

names = {
    "B1": "Regulatory Labels",
    "B2": "Clinical Trials",
    "B3": "Peer-Reviewed Lit",
    "B4": "Conference/Congress",
    "B8": "Instruments/Education",
    "B9": "Internal/DOF",
}
print("\n=== UPDATED CATEGORY DISTRIBUTION ===")
for cat in sorted(cat_dist.keys()):
    label = names.get(cat, "Other")
    count = cat_dist[cat]
    print(f"  {cat} {label:22s}: {count} docs")
print(f"\n  Total: {sum(cat_dist.values())} docs")
print("  Registry saved.")
