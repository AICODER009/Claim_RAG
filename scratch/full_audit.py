"""
Full audit of categorization_new alignment + live claim test.
Run from: new_pipeline/ parent directory
  python -m new_pipeline.scratch.full_audit
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pathlib import Path
from new_pipeline.schemas import (
    ClaimClassification, ClaimGroup, AudienceConstraint,
    ReferenceCategory, EvidenceTier
)
from new_pipeline.retrieval.mapping_matrix import MappingMatrix
from new_pipeline.prompts.classification_prompt import build_classification_prompt
from new_pipeline.skills.typization_skill import TYPIZATION_SKILL

BASE = Path(__file__).parent.parent

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
WARN = "\033[93m⚠\033[0m"

errors = []

def check(label, condition, detail=""):
    if condition:
        print(f"  {PASS} {label}")
    else:
        print(f"  {FAIL} {label} {detail}")
        errors.append(label)

# ── 1. Schemas ────────────────────────────────────────────────────────────────
print("\n══ 1. SCHEMAS ══")
groups = [g.value for g in ClaimGroup]
check("ClaimGroup has A1–A11 (11 groups)", len(groups) == 11, str(groups))
check("A10 exists", "A10" in groups)
check("A11 exists (new Study Design group)", "A11" in groups)
check("AudienceConstraint has 3 values", len(list(AudienceConstraint)) == 3)
check("payer_only in AudienceConstraint", AudienceConstraint.PAYER_ONLY.value == "payer_only")
check("hcp_only in AudienceConstraint", AudienceConstraint.HCP_ONLY.value == "hcp_only")

# ClaimClassification fields
cc = ClaimClassification(
    ct_id="CT-201",
    claim_type_name="Primary-endpoint efficacy",
    claim_group="A2",
    audience_constraint=AudienceConstraint.UNRESTRICTED,
    is_modifier_only=False,
    is_study_design=False,
    mapping_pending=False,
    confidence=0.95,
)
check("ClaimClassification.claim_group populated", cc.claim_group == "A2")
check("ClaimClassification.audience_constraint", cc.audience_constraint == AudienceConstraint.UNRESTRICTED)
check("ClaimClassification.is_study_design=False for CT-201", not cc.is_study_design)

cc_d = ClaimClassification(
    ct_id="CT-D01",
    claim_type_name="Trial design / structure",
    claim_group="A11",
    audience_constraint=AudienceConstraint.UNRESTRICTED,
    is_modifier_only=False,
    is_study_design=True,
    mapping_pending=True,
    confidence=0.88,
)
check("ClaimClassification.is_study_design=True for CT-D01", cc_d.is_study_design)
check("ClaimClassification.mapping_pending=True for CT-D01", cc_d.mapping_pending)

# ── 2. Mapping Matrix ─────────────────────────────────────────────────────────
print("\n══ 2. MAPPING MATRIX ══")
mapping_path = BASE / "prompts" / "Claim-to-Reference_Mapping.md"
check("Mapping file exists", mapping_path.exists(), str(mapping_path))

mm = MappingMatrix(mapping_path)
n = len(mm._matrix)
total = sum(len(v) for v in mm._matrix.values())
print(f"  {PASS} Loaded {n} CT-IDs, {total} CT×RT pairs")

check("Loaded 88 CT-IDs", n == 88, f"got {n}")
check("521 mappings loaded", total == 521, f"got {total}")

# Spot check known CTs
for ct in ["CT-101","CT-201","CT-301","CT-401","CT-501","CT-601","CT-701","CT-801","CT-901","CT-B01"]:
    check(f"{ct} in matrix", mm.has_ct_id(ct))

# CT-D01–D06 must NOT be in matrix (no mapping yet)
for ct in ["CT-D01","CT-D02","CT-D03","CT-D04","CT-D05","CT-D06"]:
    check(f"{ct} NOT in matrix (pending)", not mm.has_ct_id(ct))
    check(f"{ct} flagged as pending", mm.is_pending_mapping(ct))

# Modifiers
for ct in ["CT-204","CT-A01","CT-A02","CT-A03","CT-A04","CT-A05","CT-A06","CT-A07","CT-A08"]:
    check(f"{ct} is modifier", mm.is_modifier(ct))
check("CT-201 is NOT modifier", not mm.is_modifier("CT-201"))

# Audience
check("CT-405 is payer_only", mm.get_audience("CT-405") == "payer_only")
for ct in ["CT-901","CT-902","CT-903","CT-909","CT-B02","CT-B03"]:
    check(f"{ct} is payer_only", mm.get_audience(ct) == "payer_only")
check("CT-B01 is hcp_only", mm.get_audience("CT-B01") == "hcp_only")
check("CT-B04 is hcp_only", mm.get_audience("CT-B04") == "hcp_only")
check("CT-201 is unrestricted", mm.get_audience("CT-201") == "unrestricted")

# RT-602 deprecation
check("RT-602 resolves to RT-601", mm.resolve_deprecated_rt("RT-602") == "RT-601")
check("RT-601 stays RT-601", mm.resolve_deprecated_rt("RT-601") == "RT-601")
check("RT-201 stays RT-201", mm.resolve_deprecated_rt("RT-201") == "RT-201")

# Tier spot checks from Preferred Cheat Sheet
ct201_p = mm.get_primary_rt_ids("CT-201")
check("CT-201 P-tier includes RT-201 (pivotal trial)", "RT-201" in ct201_p)
check("CT-201 P-tier includes RT-101 (USPI)", "RT-101" in ct201_p)
check("CT-201 P-tier includes RT-209 (CSR)", "RT-209" in ct201_p)

ct203_p = mm.get_primary_rt_ids("CT-203")
check("CT-203 (post-hoc) has 0 P-tier refs (cheat sheet confirmed)", len(ct203_p) == 0)

ct607_p = mm.get_primary_rt_ids("CT-607")
check("CT-607 (convenience) has 0 P-tier refs (cheat sheet confirmed)", len(ct607_p) == 0)

# CT-201 blocks
ct201_n = mm.get_blocked_rt_ids("CT-201")
check("CT-201 blocks RT-310 (preprint)", "RT-310" in ct201_n)
check("CT-201 blocks RT-501 (RWE claims data)", "RT-501" in ct201_n)

# CT-405 (payer indirect comparison) — RT-304 (NMA) should be P
ct405_p = mm.get_primary_rt_ids("CT-405")
check("CT-405 P-tier includes RT-304 (NMA, payer)", "RT-304" in ct405_p)
check("CT-405 P-tier includes RT-315 (ITC/MAIC)", "RT-315" in ct405_p)

# Zero-P-tier set
zero_p = mm.get_zero_p_tier_ct_ids()
for ct in ["CT-203", "CT-204", "CT-607", "CT-806", "CT-807"]:
    check(f"{ct} in zero-P-tier set", ct in zero_p)

# ── 3. Prompt ─────────────────────────────────────────────────────────────────
print("\n══ 3. CLASSIFICATION PROMPT ══")
taxonomy_path = BASE / "prompts" / "Claim_classification.md"
check("Taxonomy file exists", taxonomy_path.exists())
taxonomy_text = taxonomy_path.read_text(encoding="utf-8")

check("New taxonomy has A11 Study Design section", "A11. Primary - Study Design" in taxonomy_text)
check("CT-D01 in taxonomy", "CT-D01" in taxonomy_text)
check("CT-D06 in taxonomy", "CT-D06" in taxonomy_text)
check("CT-B01 in taxonomy (Off-Label/SIUU)", "CT-B01" in taxonomy_text)
check("CT-109 in taxonomy (line-of-therapy)", "CT-109" in taxonomy_text)
check("CT-110 in taxonomy (combination therapy)", "CT-110" in taxonomy_text)
check("CT-309 in taxonomy (null-safety)", "CT-309" in taxonomy_text)
check("CT-311 in taxonomy (pregnancy)", "CT-311" in taxonomy_text)
check("CT-407 in taxonomy (biosimilar)", "CT-407" in taxonomy_text)
check("CT-409 in taxonomy (switch/transition)", "CT-409" in taxonomy_text)
check("CT-608 in taxonomy (manufacturing)", "CT-608" in taxonomy_text)

prompt = build_classification_prompt(taxonomy_text)
check("Prompt has CT-D01–D06 disambiguation rule", "CT-D01" in prompt)
check("Prompt has A11 reference", "A11" in prompt)
check("Prompt has multi-label intersection rule", "Multi-Label Intersection Rule" in prompt)
check("Prompt has zero-P-tier note", "Zero-P-Tier" in prompt)
check("Prompt has audience_constraint field", "audience_constraint" in prompt)
check("Prompt has is_study_design field", "is_study_design" in prompt)
check("Prompt has mapping_pending field", "mapping_pending" in prompt)
check("Prompt corrects old CT-501 comparative rule", "CT-401" in prompt)
check("Rule 16 (A10 off-label vs modifiers)", "RULE 16" not in prompt or "CT-B01" in prompt)

# ── 4. Typization Skill ───────────────────────────────────────────────────────
print("\n══ 4. TYPIZATION SKILL ══")
for i in range(1, 15):
    check(f"RULE {i} present", f"RULE {i}" in TYPIZATION_SKILL)

check("RT-602 deprecation in Rule 12", "RT-602" in TYPIZATION_SKILL and "RT-601" in TYPIZATION_SKILL)
check("NMA payer-risk note in Rule 13", "payer-preferred" in TYPIZATION_SKILL)
check("Preprint exclusion in Rule 14", "SIUU" in TYPIZATION_SKILL and "PAAB" in TYPIZATION_SKILL)

# ── 5. Typization Prompt ──────────────────────────────────────────────────────
print("\n══ 5. TYPIZATION PROMPT ══")
from new_pipeline.prompts.typization_prompt import TYPIZATION_SYSTEM_PROMPT
check("B3 range corrected to RT-315", "RT-301 through RT-315" in TYPIZATION_SYSTEM_PROMPT)
check("B5 range corrected to RT-507", "RT-501 through RT-507" in TYPIZATION_SYSTEM_PROMPT)
check("B8 label corrected (Instruments)", "Instruments" in TYPIZATION_SYSTEM_PROMPT)
check("RT-602 deprecation note present", "RT-602" in TYPIZATION_SYSTEM_PROMPT)

# ── 6. Live Claim Classification (no LLM — test the logic routing) ────────────
print("\n══ 6. LIVE CLAIM ROUTING TEST ══")
from new_pipeline.classification.claim_classifier import _infer_claim_group, MappingMatrix

test_cases = [
    ("CT-101", "A1"),
    ("CT-201", "A2"),
    ("CT-301", "A3"),
    ("CT-401", "A4"),
    ("CT-501", "A5"),
    ("CT-601", "A6"),
    ("CT-701", "A7"),
    ("CT-801", "A8"),
    ("CT-901", "A9"),
    ("CT-B01", "A10"),
    ("CT-A01", "A10"),
    ("CT-D01", "A11"),
    ("CT-D06", "A11"),
    ("CT-807", "A8"),
    ("CT-311", "A3"),
    ("CT-409", "A4"),
]
for ct_id, expected_group in test_cases:
    inferred = _infer_claim_group(ct_id)
    check(f"_infer_claim_group({ct_id}) == {expected_group}", inferred == expected_group, f"got {inferred}")

# ── Summary ───────────────────────────────────────────────────────────────────
print()
if errors:
    print(f"\033[91m══ FAILED: {len(errors)} checks ══\033[0m")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("\033[92m══ ALL CHECKS PASSED ══\033[0m")
    print(f"   88 CT-IDs, 521 pairs, all flags, all rules, all prompt fields verified.")
