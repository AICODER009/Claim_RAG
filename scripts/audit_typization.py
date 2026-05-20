"""Audit the typization registry for quality and potential hallucinations."""

import sys, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

reg = json.loads(
    Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\typization_registry.json")
    .read_text(encoding="utf-8")
)

# RED FLAG 1: Confidence uniformity
confs = [v["confidence"] for v in reg.values()]
print("=== CONFIDENCE ANALYSIS ===")
unique_confs = sorted(set(confs))
print(f"  Unique values: {unique_confs}")
print(f"  ALL identical? {len(unique_confs) == 1}")
print()

# RED FLAG 2: Suspicious classifications
print("=== POTENTIALLY WRONG CLASSIFICATIONS ===")
suspects = {
    "Argenx BVBA": "Company name — could be PI, CSR, protocol, anything",
    "CTEP Trial Development and Conduct - NCI": "NCI guide ABOUT trials, not a trial itself",
    "Van den Bergh_Eur J Neurol_2021": "This is the EAN/PNS GUIDELINE — should it be RT-305 (Practice guideline)?",
    "Mehndiratta et al. 2015": "Is this really a Cochrane systematic review?",
    "Automated Plasma Exchange (Therapeutic Plasmapheresis)": "Patient education or clinical procedure guide?",
    "Allen Supplementary APPENDIX_FINAL_02Sep2024": "Supplementary data appendix — is that a journal article?",
}

for name, note in suspects.items():
    if name in reg:
        v = reg[name]
        reason = v["reasoning"][:180]
        print(f"  FILE: {name}")
        print(f"    Result:  {v['rt_id']} ({v['category']}) - {v['reference_type_name']}")
        print(f"    Note:    {note}")
        print(f"    Reason:  {reason}")
        print()

# Show categories with counts
print("=== ALL B1 (REGULATORY) ===")
for name, v in sorted(reg.items()):
    if v["category"] == "B1":
        print(f"  {name[:60]:60s} {v['rt_id']:8s} {v['reference_type_name']}")

print("\n=== ALL B2 (CLINICAL TRIALS) ===")
for name, v in sorted(reg.items()):
    if v["category"] == "B2":
        reason = v["reasoning"][:100]
        print(f"  {name[:60]:60s} {v['rt_id']:8s} {v['reference_type_name']}")
        print(f"    Reason: {reason}")

print("\n=== ALL B4 (CONFERENCE) ===")
for name, v in sorted(reg.items()):
    if v["category"] == "B4":
        print(f"  {name[:60]:60s} {v['rt_id']:8s} {v['reference_type_name']}")

print("\n=== ALL B8 (EDUCATIONAL) ===")
for name, v in sorted(reg.items()):
    if v["category"] == "B8":
        print(f"  {name[:60]:60s} {v['rt_id']:8s} {v['reference_type_name']}")

print("\n=== ALL B9 (DOF/INTERNAL) ===")
for name, v in sorted(reg.items()):
    if v["category"] == "B9":
        reason = v["reasoning"][:100]
        print(f"  {name[:60]:60s} {v['rt_id']:8s} {v['reference_type_name']}")
        print(f"    Reason: {reason}")
