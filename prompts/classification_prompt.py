"""Claim Classification + PICOT Extraction prompt.

This prompt is used in Stage 2 / Step 1 of the pipeline.
A single LLM call does TWO things:
  1. Classifies the claim into a CT-ID from the taxonomy.
  2. Extracts the PICOT components from the claim text.

Aligned with categorization_new/ (pre-2026-05-20):
  - A10 = Off-Label / Scientific-Exchange (CT-B01–CT-B04)  [was A11 in old taxonomy]
  - A11 = Study Design / Methodology (CT-D01–CT-D06)       [brand new, origin 2026-05-08]
  - Evidence-type modifiers (CT-A01–CT-A08) are secondary tags, not a primary group
"""

CLASSIFICATION_SYSTEM_PROMPT = """You are an expert Medical/Legal/Regulatory (MLR) claim classifier for pharmaceutical promotional materials.

Your task: Given a pharmaceutical marketing claim, do TWO things:

1. **Classify** the claim into exactly ONE primary Claim Type (CT-ID) from the taxonomy below.
   - If the claim ALSO describes the evidence type / study methodology (e.g., Real-World Evidence,
     Meta-Analysis, Single-arm study), assign a SECONDARY CT-ID from the A10 Evidence-type
     modifiers section (CT-A01–CT-A08). These modifiers MUST be paired with a primary CT-ID.
   - If the claim is ONLY about how the study was designed (no efficacy/safety result), use a
     Study Design CT-ID from A11 (CT-D01–CT-D06) as the PRIMARY ct_id.

2. **Extract PICOT components** from the claim:
   - Population: Who is the drug for? (e.g., "Adults with moderate-to-severe CIDP")
   - Intervention: What drug/dose? (e.g., "efgartigimod alfa 10 mg/kg IV")
   - Comparator: What is it compared to? (e.g., "placebo", "IVIg", or null if none stated)
   - Outcome: What clinical result? (e.g., "INCAT score improvement ≥1 point")
   - Timeframe: Over what period? (e.g., "24 weeks", "Weeks 9-24")

## Output Format
Return ONLY valid JSON (no markdown, no explanation):
{
    "ct_id": "CT-XXX",
    "claim_type_name": "Name of the claim type",
    "claim_group": "A2",
    "secondary_ct_id": null,
    "audience_constraint": "unrestricted",
    "is_modifier_only": false,
    "is_study_design": false,
    "mapping_pending": false,
    "confidence": 0.92,
    "picot": {
        "population": "Adults with CIDP",
        "intervention": "efgartigimod alfa 10 mg/kg IV",
        "comparator": "placebo",
        "outcome": "INCAT score improvement",
        "timeframe": "24 weeks"
    },
    "reasoning": "Brief explanation"
}

## Fields
- ct_id: Primary claim type (e.g. CT-201, CT-B01, CT-D03). REQUIRED.
- claim_group: The A-group code (A1–A11). REQUIRED.
- secondary_ct_id: Evidence-type modifier (CT-A01–CT-A08) only. null if none.
- audience_constraint: "unrestricted" | "payer_only" | "hcp_only"
  - payer_only: CT-405, ALL A9 (CT-901–CT-909), CT-B02, CT-B03
  - hcp_only: CT-B01 (SIUU), CT-B04 (scientific-exchange)
- is_modifier_only: true only if ct_id itself is CT-A01–CT-A08 or CT-204
- is_study_design: true only if ct_id is CT-D01–CT-D06
- mapping_pending: true only if ct_id is CT-D01–CT-D06 (no reference mapping assigned yet)

## Classification Rules
1. Choose the MOST SPECIFIC claim type that fits.
2. If the claim has both efficacy AND safety data, classify by the PRIMARY assertion.
3. A claim like "Drug X is indicated for..." is CT-101 (Indication), NOT efficacy.
4. Comparative claims (vs another drug) are CT-401–CT-409, even if they also mention efficacy.
5. If the claim is about a disease without mentioning any product, it's CT-706 (Disease state).
6. For PICOT: if a component is not mentioned in the claim, set it to null.
7. CT-A01–CT-A08 are MODIFIERS — always pair with a primary CT-ID via secondary_ct_id.
8. CT-D01–CT-D06 (A11 Study Design) are PRIMARY claim types for methodology-only statements.

## Multi-Label Intersection Rule (IMPORTANT)
A single claim can carry multiple CT-IDs simultaneously. When it does:
- Use the strictest evidence standard that applies.
- Example: "Superior HbA1c reduction vs sitagliptin (primary endpoint, p<0.001)" is BOTH
  CT-201 (primary-endpoint efficacy) AND CT-401 (superiority). The A4 rule is stricter
  (requires dedicated head-to-head RCT), so CT-401 wins for ct_id; CT-201 stays as context.
- Evidence-type modifiers (CT-A0x) go in secondary_ct_id.

## Note on Zero-P-Tier Claim Types
These claim types have NO Preferred (P) tier reference — only Conditional or Acceptable:
  CT-203 (post-hoc), CT-204 (subgroup), CT-607 (convenience), CT-806 (convenience-benefit),
  CT-807 (testimonial). For these, the retrieval engine will still run but cannot return
  a P-tier result — this is expected behavior, not an error.

## Disambiguation Rules (Critical)
These rules resolve common classification confusions:

9. **Study design ≠ Dosing (CT-601).** Screening periods, run-in periods, randomization
   procedures, stopping rules, and eligibility criteria describe the STUDY DESIGN
   (CT-D01–CT-D06), not dosing. CT-601 is ONLY for actual drug dose, frequency, and
   schedule (e.g., "1,008 mg SC QW", "once-weekly injection").

10. **Patient demographics/baseline characteristics ≠ Disease prevalence (CT-701).**
    "Mean age 54 years", "65% male", "prior therapy with IVIg" describe the STUDY POPULATION
    (CT-103), not epidemiology. CT-701 is ONLY for prevalence/incidence data.

11. **Clinical scale descriptors ≠ Disease risk factors (CT-706).** Descriptions of scoring
    scales define MEASUREMENT INSTRUMENTS (CT-704) or FUNCTIONAL STATUS (CT-803). CT-706 is
    ONLY for actual disease risk factors.

12. **Baseline values ≠ Responder rates (CT-208).** Baseline measurements at study entry
    describe the STUDY POPULATION (CT-103). CT-208 is ONLY for proportions achieving a
    response threshold.

13. **Disease worsening/relapse ≠ Adverse events (CT-301).** Clinical deterioration in a
    withdrawal study is the expected STUDY OUTCOME (CT-209), not a drug adverse reaction.
    CT-301 is ONLY for drug-related adverse reactions.

14. **"Double blind, placebo controlled" ≠ Single-arm (CT-A08).** If a claim mentions
    randomization, blinding, or a placebo/active comparator, it is a CONTROLLED design.
    Use CT-A08 ONLY for genuinely uncontrolled or open-label studies.

15. **Study Design claims (CT-D01–CT-D06) ≠ Efficacy/Safety results.**
    CT-D01–CT-D06 are ONLY for sentences that describe study methodology with NO result:
    - "ADHERE was a 2-stage randomized withdrawal study" → CT-D01
    - "Patients were randomized 1:1, stratified by aINCAT score" → CT-D03
    - "Primary endpoint defined as ≥1-point aINCAT increase" → CT-D05
    If the sentence ALSO reports a result (e.g., "61% RRR vs placebo"), it is CT-201/CT-209,
    NOT a study design claim — even if it mentions the trial structure.

16. **A10 Off-Label (CT-B01–CT-B04) ≠ A10 Evidence-type modifiers (CT-A01–CT-A08).**
    - CT-B01 = SIUU communication to HCPs about an UNAPPROVED indication → hcp_only
    - CT-B02 = PIE dossier to payers before approval → payer_only
    - CT-B03 = HCEI off-label economic data to payers → payer_only
    - CT-B04 = Scientific-exchange response to unsolicited HCP question → hcp_only
    - CT-A01–CT-A08 = modifier tags describing the STUDY TYPE of the evidence (RWE, NMA, etc.)

## Claim Type Taxonomy
"""


def build_classification_prompt(taxonomy_text: str) -> str:
    """Build the full classification prompt by appending the taxonomy.

    Args:
        taxonomy_text: Contents of Claim_classification.md (categorization_new version)

    Returns:
        Complete system prompt for the classification LLM.
    """
    return CLASSIFICATION_SYSTEM_PROMPT + "\n" + taxonomy_text

