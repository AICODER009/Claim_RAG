# Claim Substantiation Requirements

**For MLR Review of Pharmaceutical Promotional Materials**

*Revisto · v1.1 · April 2026*

*Confidential – For Internal Use Only*

---

## Revision History

| Version | Date | Author | Summary of Changes |
|---|---|---|---|
| 1.0 | April 2026 | Ferry Tamtoro | Initial release — Propeller-specific hierarchy and base requirements |
| 1.1 | April 2026 | Laiba Siddiqui | Major revision: replaced fixed hierarchy with claim-type-driven routing (1.1); updated min evidentiary robustness (1.2); restructured 1.3 for MOA flexibility; added perifodic review PICOT alignment (2.3); updated implied claims language (2.4); updated anchor text requ (2.1); updated claim taxonomy (7.1) with RWE/HEOR/QoL types; added conditional met Appendix C recommendations. |

---

## Table of Contents

- [Purpose & Scope](#purpose--scope)
- [Section 1 — Reference Sourcing and Priority](#section-1--reference-sourcing-and-priority)
- [Section 2 — Claim-to-Text Matching](#section-2--claim-to-text-matching)
- [Section 3 — Coverage Score and Substantiation Completeness](#section-3--coverage-score-and-substantiation-completeness)
- [Section 4 — Numerical and Statistical Claims](#section-4--numerical-and-statistical-claims)
- [Section 5 — Multi-Reference Synthesis and Derived Conclusions](#section-5--multi-reference-synthesis-and-derived-conclusions)
- [Section 6 — Table and Figure Interpretation](#section-6--table-and-figure-interpretation)
- [Section 7 — Claim Type Classification](#section-7--claim-type-classification)
- [Section 8 — Process, Auditability and Governance](#section-8--process-auditability-and-governance)
- [Appendix A — Reference Priority Tiers by Claim Type](#appendix-a--reference-priority-tiers-by-claim-type)
- [Appendix B — Claim Type Taxonomy and Evidence Standards](#appendix-b--claim-type-taxonomy-and-evidence-standards)
- [Appendix C — Recommendations for Future Development](#appendix-c--recommendations-for-future-development)

---

## Purpose & Scope

This document defines the requirements for claim substantiation in pharmaceutical promotional materials subject to Medical, Legal, and Regulatory (MLR) review. Requirements are grounded in FDA regulatory standards (21 CFR 202.1, OPDP guidance), FTC substantiation principles, and operational learnings from live claim substantiation workflows. Each requirement includes a unique identifier, precise definition, and where applicable, the regulatory basis.

**Tag legend:**

| Tag | Meaning |
|---|---|
| **Core Requirement** | Foundational; applies universally |
| **New Requirement** | Required for AI-assisted scale workflows |
| **FDA 21 CFR 202.1 / OPDP** | Directly traceable to FDA standards |
| **FTC Guidance** | Traceable to FTC substantiation principles |

---

## Section 1 — Reference Sourcing and Priority

### 1.1 Claim-Type-Driven Decision Framework

> **Core Requirement**

Reference selection must follow a structured two-step process that first identifies the claim type, then routes to the appropriate evidence path. A fixed universal hierarchy is not prescribed, as appropriate source priority varies meaningfully by claim type.

**Step 1 — Identify Claim Type:**

- Efficacy (primary / secondary endpoint)
- Safety / tolerability
- Mechanism of action
- Dosing / administration
- Comparative / superiority
- Disease state / epidemiology
- Indication (on-label)
- Quality of life / patient-reported outcomes
- Economic / value claims
- Adherence, persistence
- Real-world evidence claims

**Step 2 — Route to Evidence Path:**

- **On-label / Indication / Safety / Dosing claim:** Primary source is the Prescribing Information (PI). If PI fully supports the claim, use PI alone (preferred). If not, supplement with pivotal trials or peer-reviewed studies.
- **Efficacy claim:** Start with pivotal trials (e.g., ORCA-2, ORCA-3). Include multiple pivotal trials when replication or evidentiary robustness is needed. Avoid lower-tier sources unless a gap exists.
- **Comparative / Superiority claim:** Use head-to-head trials and PI (if claim is in label). If no head-to-head evidence exists, use indirect comparisons only with clear qualification.
- **Mechanism of action claim:** Start with PI where mechanism is described; supplement with peer-reviewed scientific literature when deeper explanation is needed or when PI is simplified.
- **Disease state / Epidemiology claim:** Use CDC, WHO, Surgeon General Reports, and peer-reviewed epidemiology. Prefer not to use PI or product trial data.

### 1.2 Reference Set Completeness and Evidentiary Robustness

> **Core Requirement**

Use a focused set of references that collectively and completely substantiate all elements of the claim. Each reference should contribute unique, non-duplicative support.

Additional references may be included where necessary to:

- Strengthen evidentiary robustness
- Support replication across studies
- Meet regulatory expectations for substantial evidence

For example, both ORCA-2 and ORCA-3 may be cited together to demonstrate consistency across studies, even when one trial alone would suffice numerically. Redundant references that contribute no distinct element should nonetheless be removed when they add no substantive value.

### 1.3 Source-Claim Type Alignment

> **FDA 21 CFR 202.1**

The type of source used must match the type of claim being made:

- **Product-specific claims** (efficacy, safety outcomes, or branded performance statements) must be substantiated primarily using data specific to the named product — such as PI and product clinical trials.
- **Scientific or mechanistic claims** may be supported by a combination of product-specific and broader peer-reviewed literature, particularly where the mechanism is not fully described in the label or where class-level pharmacology is relevant.
- **Disease-state claims** must be supported by general scientific or public health sources (e.g., CDC, WHO, Surgeon General) and must remain clearly separated from product claims to avoid implying product efficacy.
- **Class-level or non-product-specific data** must not be used to directly substantiate product-specific performance claims unless appropriately qualified and scientifically justified.

### 1.4 Reference Currency and Version Control

> **Core Requirement**

References must be current. Superseded PI versions, retracted publications, or updated guidelines must be flagged and replaced.

Substantiation is tied to a specific document version. When a source is updated, all claims linked to the prior version must be re-verified.

**Periodic Review Cycle:** The reference library must undergo a scheduled periodic review — at minimum annually, and immediately upon PI update, major guideline revision, or trial publication. At each review cycle:

- All claims linked to sources older than 3 years must be flagged for re-validation
- A review log must record the reviewer, date, action taken (retained, updated, or escalated), and rationale
- Claims with no update action within 12 months of the last review must be automatically escalated to Medical Affairs

---

## Section 2 — Claim-to-Text Matching

### 2.1 Source Anchor Requirements

> **Core Requirement**

Each substantiation entry must include the exact source-derived anchor supporting the claim:

- Where the support is textual, the relevant portion must be captured verbatim from the source document, providing sufficient context for independent verification without reading the full source.
- For data from tables or figures, the anchor must include the derived specific data point(s) along with sufficient structural context (e.g., table title, row/column headers, figure labels) to enable independent verification.
- Multiple excerpts may be included where necessary to fully substantiate the claim, but only the minimal relevant content should be captured to maintain clarity.
- For claims involving transformation or synthesis, the relationship between the captured anchor(s) and the final claim must be clearly documented to ensure transparency and auditability.

### 2.2 Precise Location Metadata

> **Core Requirement**

Source text must be locatable via all of the following fields: file name, page number, section/paragraph heading, and sentence index.

"Section 14" alone is insufficient — the paragraph and sentence must identify exactly where within that section the text appears.

Tables and figures require additional specificity (see Section 6 for detailed requirements).

*Note: Not all source types support all location fields. See Section 8.1 for the mandatory vs. conditional metadata schema by source type.*

### 2.3 Contextual Relevance — PICOT Alignment

> **Core Requirement**

The substantiating evidence must align with the claim across all applicable PICOT dimensions:

- **Population:** Evidence must reflect the same population as the claim. Subgroup data must not be generalized to broader populations unless explicitly stated and justified.
- **Intervention:** The intervention described in the evidence must match the product and use described in the claim.
- **Comparator:** The comparator must match exactly. Results from placebo-controlled studies must not be used to imply superiority over an active comparator.
- **Outcome (Endpoint):** The endpoint definition (e.g., continuous abstinence vs. point prevalence) must match the claim. Secondary or exploratory endpoints must not be presented as primary outcomes without clear labeling.
- **Timeframe:** The duration or assessment window in the claim must match the source. Minor approximations may be acceptable if they do not alter interpretation (e.g., "~12 weeks" for a 9-12 week endpoint), but material differences require explicit qualification.

Where exact alignment is not present, any deviation must be transparently qualified in the claim to avoid misleading interpretation.

### 2.4 Implied Claim Coverage (Net Impression)

> **FTC Guidance**

References must substantiate not only the explicit statement of a claim but also its key implied meanings, as interpreted from the perspective of the intended audience.

Implied meanings include any information that a reasonable reader would infer from the claim, such as:

- Magnitude of effect
- Comparator context
- Statistical significance
- Duration and population applicability

For example, relative claims (e.g., "4x more likely to quit") require support for both the underlying rates and the comparator from which the ratio is derived. Both the numerator rate and denominator (e.g., placebo rate) must be findable in the cited source.

Where implied meanings are not directly supported by the cited evidence, the claim must be modified, qualified, or rejected to avoid creating a misleading net impression. The FTC principle of "net impression" applies — claims are evaluated from the standpoint of the intended audience.

---

## Section 3 — Coverage Score and Substantiation Completeness

### 3.1 Per-Claim Coverage Score

> **New Requirement**

Each claim receives a coverage score (0–100) representing how completely the cited references address every distinct sub-assertion in the claim.

A claim with three distinct factual elements (population, rate, comparator) requires all three to be explicitly present in cited text to achieve a score of 100. Partial coverage yields a proportional score — e.g., if rate is present but comparator is missing, the score is approximately 67.

**Important:** Coverage scores are designed as a prioritization and triage tool for human reviewers — they are a gauge, not an absolute determination of claim validity. Scientific substantiation cannot be reduced to arithmetic; two claims scoring identically may differ meaningfully in evidentiary quality. Coverage scores should prompt reviewer attention, not replace it.

### 3.2 Combined Reference Coverage

> **New Requirement**

When a claim is substantiated across multiple references, the combined coverage score is computed as the union of sub-assertions covered across all cited sources.

References must be non-redundant — if two references cover the same sub-assertion, only one counts toward coverage. The system must flag redundant references for removal to enforce minimum-reference discipline, while permitting retention where additional references serve evidentiary robustness (see 1.2).

### 3.3 Coverage Thresholds and Escalation

> **New Requirement**

Claims must reach a minimum combined coverage score of 80 to proceed to MLR review.

- **Score ≥80:** Proceed to MLR review
- **Score 60–79:** Soft flag — reviewer annotation required explaining the gap
- **Score <60:** Blocked — returned for re-substantiation

Coverage score is recalculated automatically whenever references are added, replaced, or modified.

### 3.4 Portfolio-Level Coverage Summary

> **New Requirement**

A coverage report is generated per material showing: total claims, fully covered (≥80), partially covered (60–79), uncovered (<60), and mean coverage score.

This enables MLR reviewers to prioritize attention and identify systemic gaps in the reference library before the formal review begins.

---

## Section 4 — Numerical and Statistical Claims

### 4.1 Exact Figure Traceability

> **Core Requirement**

Every percentage, ratio, count, or p-value in a claim must be traceable to an identical figure in the source. If the source gives "32%" and the claim says "approximately one-third," this constitutes an indirect transformation requiring explicit documentation (see 4.2).

### 4.2 Indirect Transformation and Calculation Documentation

> **New Requirement**

Claims derived by calculation from source data must document the transformation logic: source value → transformation type → claim value. Examples:

- "~5x" from OR=5.3 → rounding transformation
- "more than half" from 53.3% → directional summary
- "nearly 80%" from 78.2% → rounding transformation
- "4x more likely" from 32% ÷ 8% → ratio derivation

**Permissible transformations:** rounding, ratio derivation, directional summary.

**Not permissible:** extrapolations beyond the study timeframe; combining results across non-pre-specified populations.

**Rounding tolerance guidance:** Approximations within ±2 percentage points of the source value are generally permissible. Approximations beyond ±5 percentage points require explicit justification. All rounding must be directionally conservative (i.e., must not overstate efficacy or understate risk).

### 4.3 Statistical Context Preservation

> **FDA OPDP**

Efficacy claims must preserve the material statistical context of the source to ensure accurate interpretation. This includes alignment with the original:

- Endpoint definition and assessment window (e.g., "weeks 9–12", not just "12 weeks")
- Comparator and measurement or verification method (e.g., CO-confirmed vs. self-reported)
- Effect measure and statistical significance, where these influence the meaning of the result

Claims must not omit or alter contextual qualifiers in a way that could change the interpretation of the data. Where statistical significance or comparative effect is stated or implied (e.g., "significantly improved," "more effective"), appropriate statistical support (p-value, confidence interval, or effect measure) must be available in the cited source.

Presentation of detailed statistical metrics is not required in all cases, but must not be contradicted or obscured by the claim. In space-constrained formats, essential context may be presented through accompanying references or disclosures, provided the overall communication does not create a misleading impression.

### 4.4 Comparator Specificity

> **21 CFR 202.1(e)**

Claims involving a comparator must reflect the exact comparator and study arm used in the cited source:

- The comparison presented in the claim must match the comparison evaluated in the underlying evidence, including population, endpoint, and timeframe.
- Results from placebo-controlled trials must not be used to imply or suggest superiority over an active comparator unless such a comparison is directly supported by head-to-head evidence or appropriately qualified indirect comparison methods.
- Relative claims (e.g., "4x more likely") must clearly specify the reference baseline and be derived from comparable data points within the same study context.
- Claims that imply a comparison (e.g., "improved outcomes") must be supported by an identifiable comparator in the cited evidence, even if not explicitly stated in the claim.
- For studies with multiple comparator arms, the claim must clearly correspond to the specific comparator arm from which the data are drawn.

Indirect or cross-study comparisons must be clearly identified as such and appropriately qualified to avoid misleading interpretation.

---

## Section 5 — Multi-Reference Synthesis and Derived Conclusions

### 5.1 Permissible Multi-Reference Combination

> **New Requirement**

A claim may be substantiated by combining two or more references only when each reference independently establishes one distinct component of the claim — and when the logical combination does not create a new unstated conclusion.

*Example:* Combining VanFrank MMWR 2024 (chronic/relapsing framing) + SGR 2020 (treatability) to substantiate "chronic, treatable condition" is permissible because each reference adds a distinct, non-overlapping assertion.

### 5.2 Impermissible Inference Chains

> **FDA OPDP**

References cannot be combined to produce a conclusion that neither reference individually asserts. OPDP enforcement consistently flags pooling data from two non-significant trials to create a composite significant result.

The combined conclusion must be explicitly stated in at least one cited source, or the combination must be a simple logical union of two non-overlapping, independently validated facts.

### 5.3 Synthesis Documentation

> **New Requirement**

When two or more references are combined to derive a conclusion, the synthesis logic must be documented:

- For each reference, which element it contributes
- Why the combined assertion is scientifically valid

This creates an auditable chain of reasoning. A list of citations without explicit element-to-reference mapping is insufficient.

---

## Section 6 — Table and Figure Interpretation

### 6.1 Table-Sourced Claims

> **New Requirement**

When a claim derives from a data table, the substantiation must identify:

- Table number and/or title
- Specific row and column (or cell) from which the value is drawn
- Relevant headers, labels, and footnotes necessary to interpret the value (e.g., population, endpoint definition, units, timeframe)

Citing a table without specifying the exact data location (e.g., "Table 2") is insufficient.

The captured anchor must include the data value along with minimal necessary contextual elements to allow independent verification without reviewing the entire table.

For complex tables (e.g., multi-level headers, subgroup analyses), the specific level of data used must be clearly identified to avoid ambiguity or misinterpretation.

Where claims are derived from multiple table values (e.g., ratios or comparisons), each contributing data point must be explicitly identified and linked to the transformation logic (see 4.2).

### 6.2 Figure and Graph Interpretation

> **New Requirement**

When a claim derives from a figure (bar chart, forest plot, Kaplan-Meier curve, etc.), the reference must identify: the figure number/title, which data series or axis value supports the claim, and whether the numerical value is a labeled data point or estimated from the scale.

Visual estimation from unlabeled figures must be explicitly flagged as an approximation, and the estimated value must be accompanied by a margin of uncertainty.

*Note: A separate companion document defining requirements for ingesting and interpreting reference documents (including visual data extraction protocols) is planned to supplement this section.*

### 6.3 Subgroup and Forest Plot Data

> **Core Requirement**

Claims citing subgroup analyses must:

- Clearly identify whether the subgroup was pre-specified or post-hoc
- Include the subgroup-specific effect estimate (e.g., odds ratio, hazard ratio, risk difference) and corresponding confidence interval
- For claims implying differential treatment effects across subgroups, be supported by a statistically significant interaction test — differences in point estimates alone are insufficient
- Present post-hoc subgroup findings with appropriate qualification (e.g., exploratory or hypothesis-generating); these must not be used as primary or headline claims without strong supporting evidence
- Consider the potential for multiplicity and false-positive findings when multiple subgroup analyses are conducted; selective emphasis on favorable subgroups must be avoided

For forest plot-derived claims, the specific subgroup, effect estimate, and confidence interval must be clearly identified, and the claim must remain consistent with the overall study findings and context.

### 6.4 CSR Figure Traceability

> **Core Requirement**

Data drawn exclusively from Clinical Study Reports that appear only in unpublished internal figures must be labeled as "data on file" and linked to the specific section number, figure number, and narrative context within the CSR.

These require additional reviewer scrutiny given their non-public status and inability to undergo external peer review.

---

## Section 7 — Claim Type Classification

### 7.1 Claim Type Taxonomy

> **Core Requirement**

Each claim must be classified as one of the following types. Classification drives which evidence tier is required and which regulatory standard applies:

- Efficacy (primary endpoint)
- Efficacy (secondary endpoint)
- Efficacy (subgroup analysis)
- Safety / tolerability
- Mechanism of action
- Dosing / administration
- Comparative / superiority (including non-inferiority and equivalence claims vs. a defined comparator)
- Disease state / epidemiology
- Indication (on-label)
- Quality of life / patient-reported outcomes
- Economic / value claims (where applicable)
- Adherence or persistence claims (where applicable)
- Real-world evidence claims (where applicable)

### 7.2 Comparative Claim Standard

> **21 CFR 202.1(e)**

Any claim that directly or implicitly compares the product to another therapy must be substantiated by a head-to-head study or explicit approved label language.

Indirect comparisons require prominent qualification. FDA requires valid, reliable data for comparative claims — cross-trial comparisons or observational data are insufficient without explicit caveats.

### 7.3 Disease State Claim Separation

> **Core Requirement**

Claims about the disease state (e.g., "nicotine dependence is a chronic condition") must be sourced from general scientific literature — not from product-specific trial data — and must not imply product efficacy by proximity to the product claim.

Reference hierarchy for disease state claims: SGR > CDC/health authority guidance > peer-reviewed epidemiology.

### 7.4 On-Label Boundary Enforcement

> **FDA OPDP**

No claim may assert, imply, or be reasonably interpreted to promote an indication, population, or use not reflected in the current approved PI.

Mechanism language must not overstate the clinical implication. Off-label information triggers mandatory escalation to regulatory review and cannot proceed without explicit Medical Affairs authorization.

---

## Section 8 — Process, Auditability and Governance

### 8.1 Citation Metadata Schema (Mandatory vs. Conditional Fields)

> **Core Requirement**

**Core mandatory fields (apply to all source types):**

- Full citation (author, title, source, year)
- File name as stored in the reference library
- Page number
- Verbatim anchor text (or data anchor — see Section 2.1)

**Conditional fields by source type:**

| Field | Journal / PI | Congress Poster | CSR |
|---|---|---|---|
| DOI / Volume / Page range | Required | If available | N/A |
| Section / paragraph heading | Required | Required | Required |
| Sentence index | Required | If applicable | Required |
| Table / Figure number | If applicable | If applicable | If applicable |
| "Data on file" label | N/A | N/A | Required |
| Preliminary data flag | N/A | Required | N/A |

All mandatory fields are required for MLR submission. Missing mandatory fields block submission. Missing conditional fields that apply to the source type must be flagged with a reason for absence.

### 8.2 Reviewer Accountability and Audit Trail

> **Core Requirement**

Each substantiation entry must record the reviewer who assigned it, the date assigned, and any reviewer comments. Changes to existing substantiation (text edits, reference swaps, coverage score overrides) must create an immutable audit trail with the prior state preserved.

This supports both internal governance and potential FDA inspection.

### 8.3 Substantiation Stability on Modular Reuse

> **Core Requirement**

When a claim is reused across multiple materials (modular content), the substantiation is inherited but must be re-validated against current PI and reference versions at the time of each new material submission.

Cross-material consistency checks must confirm that the same claim is not substantiated by different or inconsistent references across different assets.

### 8.4 Fair Balance Linkage

> **FDA 21 CFR 202.1(e)(5)**

For every efficacy or mechanism claim substantiated, the system must confirm that corresponding safety/risk information (adverse events, warnings, contraindications) from the same or equivalent section of the PI is also referenced in the material.

Substantiation of benefit claims is incomplete without verifiable fair balance linkage.

### 8.5 Unsubstantiated Claim Blocking and Escalation

> **Core Requirement**

Claims submitted without any reference must be automatically flagged as unsubstantiated and blocked from MLR submission.

The system must offer a reference suggestion workflow based on semantic matching to the approved claims library. If no adequate reference exists, the claim must be escalated to Medical Affairs for determination: proceed with additional data, modify the claim, or remove it entirely.

### 8.6 Reference Library Governance and Periodic Review

> **Core Requirement**

The reference library must be maintained as a controlled document set with version history. New publications are added upon PI approval, trial publication, or guideline update. Expired, retracted, or superseded documents are archived rather than deleted. All claims linked to archived documents are automatically flagged for re-substantiation review.

**Periodic Review Cycle:** In addition to event-triggered updates (see 1.4), the reference library must be reviewed on a defined periodic schedule:

- **Annual full review:** All references assessed for currency, relevance, and continued adequacy
- **Quarterly spot check:** High-priority references (PI, pivotal trials) verified against any updates
- **Review log:** Records reviewer identity, date, action taken, and rationale for each document reviewed
- **Escalation:** Any reference with no review activity within 12 months is automatically escalated for Medical Affairs attention

---

## Appendix A — Reference Priority Tiers by Claim Type

The table below maps claim types to their appropriate reference tiers. Priority within each claim type is listed from highest to lowest authority.

| Tier | Source Type | Claim Types Supported | Notes |
|---|---|---|---|
| 1 (Highest) | Prescribing Information (PI) | Indication, dosing, mechanism, safety, contraindications, drug interactions | Approved label — highest authority; directly traceable to FDA approval. Sole authority for dosing claims. |
| 2 | Peer-reviewed pivotal trials | Efficacy primary/secondary endpoints, safety profile, study design, baseline characteristics | Both ORCA-2 and ORCA-3 required for pooled claims. Multiple trials strengthen evidentiary robustness. |
| 3 | Clinical Study Reports (CSRs) | CV safety, weight change, anxiety/depression, unpublished subgroup analyses | "Data on file" — non-public; requires additional reviewer scrutiny. |
| 4 | Other published studies | Subgroup analyses, disease mechanism, pharmacology | Document pre-specified vs. post-hoc status. May be used to supplement PI or pivotal trials. |
| 5 | Congress / meeting presentations | Pooled subgroup analyses, preliminary data | Not yet peer-reviewed; flag as preliminary data; supplement with published sources when available. |
| 6 | Health guidance reports (e.g., US Surgeon General) | Disease state framing, treatability, clinician intervention | Authoritative but not product-specific. Do NOT use for efficacy claims. |
| 7 (Lowest) | Other health guidance (AHA, CDC, ACS, WHO) | Population statistics, quitting benefits, disease epidemiology | For disease state and general health claims only. Never use for product efficacy. |

---

## Appendix B — Claim Type Taxonomy and Evidence Standards

| Claim Type | Example Claims | Required Sources | Key Standard |
|---|---|---|---|
| Efficacy – primary endpoint | CO-confirmed continuous abstinence rates at primary window | PI Section 14, pivotal trials | Substantial evidence (≥2 adequate and well-controlled trials) |
| Efficacy – secondary endpoint | Long-term abstinence through Week 24; cotinine levels; 7-day PPA | PI Section 14 (secondary), pivotal trials | Same standard; must not be presented as primary unless labeled |
| Efficacy – subgroup | COPD patients; prior quit attempts; prior pharmacotherapy | SRNT pooled abstract; Prochaska Thorax; CSR subgroup analyses | Note pre-specified vs. post-hoc; add caveat if post-hoc; interaction test required for differential effect claims |
| Safety / tolerability | AE rates, discontinuation rates, SAEs, NPS events | PI Section 6.1 (pooled), pivotal trial safety tables, CSRs | Must match exact trial population and timeframe |
| Mechanism of action | α4β2 nAChR partial agonist/antagonist; dopamine modulation | PI Section 12.1; Benowitz NEJM 2010; class-level pharmacology literature | Cannot overstate clinical implication. Scientific literature permitted where PI is simplified. |
| Dosing / administration | Dose, frequency, renal adjustment, titration, quit date timing | PI Sections 2.1, 2.2 | PI is sole authority; no inferencing from trial protocols |
| Comparative / superiority | Lower nausea vs. varenicline; first new option in 20 years | Head-to-head trial data; PI (if claim is in label) | Head-to-head data or label language required; indirect comparisons need prominent caveats |
| Disease state / epidemiology | Chronic/relapsing condition; 28.8M smokers; quit attempt statistics | VanFrank MMWR 2024; Benowitz NEJM; SGR 2020; CDC/WHO guidance | General scientific literature only; must not imply product efficacy by proximity |
| Indication | FDA-approved for smoking cessation in adults | PI Section 1 | Verbatim from PI only; no embellishment or scope expansion |
| Contraindications / warnings | Hypersensitivity; NPS monitoring; pregnancy | PI Sections 4, 5, 8.1 | Verbatim from PI; required for fair balance with efficacy claims |
| Quality of life / PRO | Patient-reported satisfaction; withdrawal symptom burden | Validated PRO instruments from pivotal trials or published studies | Must reference validated instrument; endpoint must be pre-specified |

---

## Appendix C — Recommendations for Future Development

The following areas were identified during stakeholder review as requiring additional specification or as adjacent documents to be developed in parallel:

### C.1 Reference Document Ingestion and Interpretation Protocol

A companion specification is needed to define how reference documents — particularly those containing figures, forest plots, tables, and Kaplan-Meier curves — are ingested, rendered, and interpreted by the substantiation system. This document should address:

- Standards for visual data extraction (labeled vs. estimated data points)
- Forest plot and subgroup data interpretation rules
- Handling of unpublished or restricted CSR figures
- Protocols for congress poster ingestion (preliminary data handling)

### C.2 Rounding and Approximation Tolerance Policy

A formal rounding tolerance policy should be developed to define acceptable approximation bounds for numerical transformations. This policy should specify:

- Absolute tolerance thresholds by claim type (e.g., ±2% for rates, ±0.1 for ORs)
- Directional conservatism requirements (approximations must not overstate efficacy or understate risk)
- Flag-and-review triggers for transformations that exceed tolerance

### C.3 AI-Assisted Substantiation QA Framework

As AI-assisted substantiation is deployed at scale, a QA framework should be developed to validate coverage score robustness, test for context-stripping errors, and audit synthetic transformation logic. This framework should include:

- Test cases for each claim type with known correct and incorrect substantiations
- Red-team scenarios designed to expose common failure modes (e.g., implied claim misses, PICOT misalignment)
- Periodic human reviewer calibration against AI outputs

### C.4 Real-World Evidence and Economic Claims Standards

As real-world evidence (RWE) and health economics / outcomes research (HEOR) claims become more common in promotional materials, dedicated substantiation standards are needed for:

- RWE study design adequacy thresholds
- Acceptable comparator constructs in observational data
- HEOR model transparency and assumption disclosure requirements
