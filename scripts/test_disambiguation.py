"""Re-classify the previously misclassified claims with updated disambiguation rules.
Compares old (wrong) vs new (hopefully correct) classification.
"""
import sys, os, json, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\revisto_evidence_aligned_clean")

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\.env"))

from new_pipeline.classification.claim_classifier import ClaimClassifier
from new_pipeline.config import load_config

cfg = load_config()

classifier = ClaimClassifier(
    provider="anthropic",
    model="claude-sonnet-4-20250514",
    api_key=cfg.llm.anthropic_api_key,
    taxonomy_path=cfg.claim_classification_path,
)

# The 40 claims that were misclassified, with their CORRECTED CT-IDs
test_cases = [
    # (row, claim_text, old_wrong_ct, correct_ct, reason)
    (411, "Randomized withdrawal period Double blind, placebo controlled (Stage B)", "CT-A08", "CT-201", "controlled study, not single-arm"),
    (550, "Based on published policies from Policy Reporter as of December 2024.", "CT-201", "NON-CLAIM", "source attribution"),
    (415, "The screening period was for a maximum of 4 weeks, and the run-in period was for a maximum of 12 weeks.", "CT-601", "CT-A08", "study design, not dosing"),
    (424, "If patients had clinical deterioration (relapse), then their participation in the randomized withdrawal period ended.", "CT-601", "CT-A08", "stopping rule, not dosing"),
    (421, "Patients who had evidence of improvement at 2 consecutive visits were eligible to proceed to the randomized withdrawal period.", "CT-601", "CT-103", "eligibility criteria"),
    (417, "Patients who were on treatment at screening had been receiving standard-of-care therapy (IVIG, SCIG, or corticosteroids).", "CT-701", "CT-103", "prior treatment, not prevalence"),
    (430, "Mean age, years (SD) 54 (14) 55 (13) 51 (14)", "CT-701", "CT-103", "demographics, not prevalence"),
    (432, "Mean time since diagnosis, years (SD) 5 (6) 4 (4) 4 (5)", "CT-701", "CT-103", "demographics"),
    (434, "Immunoglobulins (IVIG, SCIG) 165 (51) 48 (43) 48 (44)", "CT-701", "CT-103", "prior treatment data"),
    (435, "Not receiving treatment (including treatment naive) 94 (29) 39 (35) 39 (36)", "CT-701", "CT-103", "treatment status"),
    (553, "5: Restricted to wheelchair, unable to stand and walk a few steps with help", "CT-706", "CT-704", "disability scale descriptor"),
    (1034, "5 Restricted to wheelchair, unable to stand and walk a few steps with help", "CT-706", "CT-704", "disability scale"),
    (1037, "Usually uses unilateral support (stick, single crutch, 1 arm) to walk outdoors", "CT-706", "CT-704", "disability scale"),
    (758, "Use your clinical judgment to determine the appropriate amount of refills for your patient.", "CT-706", "CT-601", "dosing instruction"),
    (437, "Mean clinical status scores (SD): aINCAT 4.6 (1.67), I-RODS 40.1 (14.67)", "CT-208", "CT-103", "baseline data"),
    (438, "Grip strength (dominant hand), kPa 38.5 (24.18)", "CT-208", "CT-103", "baseline data"),
    (439, "Grip strength (nondominant hand), kPa: 39.0 (24.71)", "CT-208", "CT-103", "baseline data"),
    (552, "An INCAT arm disability score that changed from 0 to 1 or from 1 to 0 was not incorporated into the overall adjusted INCAT score.", "CT-208", "CT-704", "measurement methodology"),
    (407, "Patients discontinued treatment and demonstrated evidence of deterioration", "CT-301", "CT-A08", "disease worsening, not AE"),
    (441, "Clinical characteristics of the randomized withdrawal period were similar between treatment groups", "CT-301", "CT-103", "baseline comparability"),
]

print(f"Testing {len(test_cases)} previously misclassified claims with updated prompt")
print(f"Using: anthropic / claude-sonnet-4-20250514")
print("=" * 90)
print(f"{'Row':>5} | {'Old(wrong)':>12} | {'Expected':>12} | {'New Result':>12} | {'Match':>5} | Claim")
print("-" * 90)

correct = 0
wrong = 0
results = []

for row, claim, old_ct, expected_ct, reason in test_cases:
    try:
        classification, picot = classifier.classify(claim)
        new_ct = classification.ct_id
        
        # Check if new classification matches expected
        match = new_ct == expected_ct
        if match:
            correct += 1
            marker = "  ✓"
        else:
            wrong += 1
            marker = "  ✗"
        
        print(f"{row:>5} | {old_ct:>12} | {expected_ct:>12} | {new_ct:>12} | {marker} | {claim[:60]}")
        results.append({"row": row, "old": old_ct, "expected": expected_ct, "new": new_ct, "match": match})
        
    except Exception as e:
        wrong += 1
        print(f"{row:>5} | {old_ct:>12} | {expected_ct:>12} | {'ERROR':>12} | {'  ✗'} | {str(e)[:60]}")
    
    time.sleep(0.3)

print("=" * 90)
print(f"RESULTS: {correct}/{len(test_cases)} now correct ({correct/len(test_cases)*100:.0f}%)")
if wrong > 0:
    print(f"Still wrong: {wrong}")
    for r in results:
        if not r["match"]:
            print(f"  Row {r['row']}: expected {r['expected']}, got {r['new']}")
