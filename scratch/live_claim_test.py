"""
Live claim classification test using real API.
Tests one claim from each major group through the full classify() pipeline.
"""
import sys, os
sys.path.insert(0, '..')
os.chdir(r'c:\Users\User\Downloads\new_pipeline\new_pipeline')

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(r'c:\Users\User\Downloads\new_pipeline\new_pipeline\.env')

from new_pipeline.classification.claim_classifier import ClaimClassifier
from new_pipeline.schemas import AudienceConstraint

BASE = Path(r'c:\Users\User\Downloads\new_pipeline\new_pipeline')
TAXONOMY = BASE / 'prompts' / 'Claim_classification.md'

api_key = os.getenv('OPENAI_API_KEY', '')
model = os.getenv('CLASSIFIER_MODEL', 'gpt-4o-mini')

classifier = ClaimClassifier(
    provider='openai',
    model=model,
    api_key=api_key,
    taxonomy_path=TAXONOMY,
)

TEST_CLAIMS = [
    # (claim_text, expected_group, expected_ct_prefix, description)
    (
        "VYVGART Hytrulo reduced the risk of relapse by 61% vs placebo (p<0.001) "
        "in the primary endpoint of the ADHERE trial.",
        "A2", "CT-201", "Primary efficacy"
    ),
    (
        "ADHERE was a 2-stage study: Stage A was an open-label run-in period, "
        "and Stage B was a randomized withdrawal period.",
        "A11", "CT-D01", "Study design (A11)"
    ),
    (
        "Patients were randomized 1:1 to VYVGART Hytrulo or placebo, "
        "stratified by aINCAT score at baseline.",
        "A11", "CT-D03", "Randomization & blinding (A11)"
    ),
    (
        "VYVGART Hytrulo is indicated for the treatment of adults with "
        "chronic inflammatory demyelinating polyneuropathy (CIDP).",
        "A1", "CT-101", "Indication claim"
    ),
    (
        "The most common adverse events were injection-site reactions (15%) "
        "and headache (12%).",
        "A3", "CT-301", "AE profile"
    ),
]

print(f"\nLive classification using model: {model}")
print(f"Taxonomy: {TAXONOMY.name} ({len(TAXONOMY.read_text(encoding='utf-8'))} chars)\n")
print("=" * 70)

all_pass = True
for claim, exp_group, exp_ct_prefix, desc in TEST_CLAIMS:
    print(f"\n[{desc}]")
    print(f"  Claim: {claim[:80]}...")
    
    classification, picot = classifier.classify(claim)
    
    ct_ok = classification.ct_id.startswith(exp_ct_prefix)
    grp_ok = classification.claim_group == exp_group
    
    status = "PASS" if (ct_ok and grp_ok) else "FAIL"
    if status == "FAIL":
        all_pass = False
    
    print(f"  CT-ID:          {classification.ct_id}  (expected prefix {exp_ct_prefix}) -> {['FAIL','PASS'][ct_ok]}")
    print(f"  Group:          {classification.claim_group}  (expected {exp_group}) -> {['FAIL','PASS'][grp_ok]}")
    print(f"  Claim type:     {classification.claim_type_name}")
    print(f"  Audience:       {classification.audience_constraint.value}")
    print(f"  is_study_design:{classification.is_study_design}")
    print(f"  mapping_pending:{classification.mapping_pending}")
    print(f"  is_modifier:    {classification.is_modifier_only}")
    print(f"  confidence:     {classification.confidence:.2f}")
    print(f"  PICOT pop:      {picot.population}")
    print(f"  PICOT outcome:  {picot.outcome}")
    print(f"  -> {status}")

print("\n" + "=" * 70)
print(f"\n{'ALL CLAIMS PASSED' if all_pass else 'SOME CLAIMS FAILED'}")
