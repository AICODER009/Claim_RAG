"""Typization Skill — domain-expert rules for reference document classification.

This skill is injected into the typization prompt AFTER the taxonomy.
It encodes edge-case patterns from pharmaceutical/medical document
classification that the base taxonomy alone cannot catch.

USAGE:
    from new_pipeline.skills.typization_skill import TYPIZATION_SKILL
    full_prompt = build_typization_prompt(taxonomy_text) + "\n" + TYPIZATION_SKILL
"""

TYPIZATION_SKILL = '''

## SKILL: Pharma/Medical Document Typization Expert Rules

These rules are mandatory overrides learned from validated classifications.
Apply them BEFORE falling back to generic taxonomy matching.

### RULE 1: Guidelines Published in Journals → RT-311, NOT RT-301

Clinical practice guidelines are often published IN peer-reviewed journals
(e.g., European Journal of Neurology, Neurology, JAMA). They look like
journal articles but ARE NOT primary research. They are consensus
recommendations from medical societies.

**Detection signals:**
- Title contains: "guideline", "recommendations", "consensus", "position statement",
  "best practice", "standards of care", "diagnostic criteria"
- Authors include a working group or task force (e.g., "Task Force",
  "Practice Parameter Committee", "Evidence-Based Guideline Subcommittee")
- Abstract mentions: "evidence-based recommendations", "expert consensus",
  "Delphi process", "GRADE methodology"
- Often cite GRADE or Oxford CEBM levels of evidence

**Action:** Classify as RT-311 (specialty-society clinical practice guideline), category B3.
**NOT** RT-301 (peer-reviewed journal article).

**Few-shot examples (generic):**
- "EAN/PNS Guideline on diagnosis and treatment of [disease]", Eur J Neurol → RT-311
- "AAN Practice Parameter: Treatment of [condition]", Neurology → RT-311
- "EFNS/PNS Management Guidelines for [disease]", J Peripher Nerv Syst → RT-311


### RULE 2: Methodology Guides ≠ Clinical Trials

Documents that describe HOW to conduct trials (design, methodology, statistical
approaches) are NOT clinical trial reports themselves.

**Detection signals:**
- Title contains: "guidance", "methodology", "how to", "development and conduct",
  "best practices for trial design"
- Content is prescriptive/instructional rather than reporting results
- No patient enrollment numbers, no efficacy endpoints, no safety data

**Action:** Classify as RT-311 (B3) or RT-306 (narrative review, B3).
**NOT** RT-201/RT-202/RT-208 (clinical trial categories, B2).

**Few-shot examples (generic):**
- "Trial Development and Conduct Manual", NCI → RT-311 (NOT RT-201)
- "ICH E6 Good Clinical Practice Guideline" → RT-311 (NOT B2)
- "FDA Guidance for Industry: Adaptive Trial Design" → RT-311 (NOT B2)


### RULE 3: Conference Detection — Check Filename AND Body

Conference posters/presentations often don't contain the word "poster"
in their body text. The strongest signals are:

**Filename signals (high specificity):**
- AAN, AANEM, EAN, ECTRIMS, ANA, WCN → neurology conferences
- ASH, ASCO, ESMO → oncology conferences
- ACR, EULAR → rheumatology conferences
- "poster", "oral", "presentation", "abstract" in filename

**Body text signals:**
- Structured as: INTRODUCTION → METHODS → RESULTS → CONCLUSIONS (no Discussion)
- Single page or poster layout
- Numbered superscript affiliations
- QR code or "Scan for references"
- "Presented at [Conference Name]"
- Disclosure/conflict-of-interest section at bottom

**Action:** If filename contains a conference abbreviation → RT-402 (poster) or
RT-403 (oral presentation). Only use RT-401 (abstract) if the document is
clearly just the abstract text without poster/slide content.

**Few-shot examples (generic):**
- "Smith_AAN_2024_Poster.pdf" with IMRC structure → RT-402 (poster)
- "Jones et al EAN 2023 Oral Presentation.pdf" → RT-403 (oral)


### RULE 4: Data on File (DOF) — Strict Identification

DOF documents are internal, unpublished company data. They should ONLY be
classified as RT-901 when:

**Required signals (need at least 2):**
- "Data on File" or "DOF" or "DoF" in filename or title
- Internal reference number (e.g., "REF-XXXXX")
- Watermark or header saying "CONFIDENTIAL" or "Data on File"
- No journal name, no DOI, no peer review indicators
- Company-specific formatting

**Warning:** A document from a pharmaceutical company is NOT automatically
DOF. It could be a protocol (RT-208/210), CSR (RT-209), or IB (RT-213).
Read the content.

**Few-shot examples (generic):**
- "REF-04567_DOF_Efficacy_Summary_2025.pdf" with internal data → RT-901
- "Pharma Corp" (company name only, but content is a protocol) → RT-208 (NOT RT-901)


### RULE 5: Prescribing Information — Unambiguous Markers

These are the most reliably classified documents. Look for:
- "HIGHLIGHTS OF PRESCRIBING INFORMATION" → RT-101 (USPI)
- "FULL PRESCRIBING INFORMATION" section structure → RT-101
- "INDICATIONS AND USAGE" + "DOSAGE AND ADMINISTRATION" + "WARNINGS" → RT-101
- "Instructions for Use" as standalone → RT-104 (IFU)
- "Important Safety Information" standalone flyer → classify based on source label

**Few-shot examples (generic):**
- "drug-name-prescribing-information.pdf" with FDA sections → RT-101
- "Drug Name Instructions For Use (IFU).pdf" → RT-104
- "Drug Name Important Safety Information.pdf" (derived from PI) → RT-101


### RULE 6: Systematic Reviews vs. Regular Reviews

**Systematic review (RT-302):**
- Follows PRISMA or Cochrane methodology
- Has explicit search strategy (databases searched, keywords, date range)
- PRISMA flow diagram
- Quality assessment / risk of bias table
- "Cochrane Database" in journal name → always RT-302

**Narrative/regular review (RT-306):**
- No systematic search methodology
- Author-selected references
- Opinion-based synthesis
- "Review" in title but no PRISMA

**Meta-analysis (RT-303):**
- All signals of RT-302 PLUS forest plots / pooled effect sizes

**Few-shot examples (generic):**
- "Immunoglobulins for [disease]: A Cochrane Review" → RT-302
- "[Treatment] in [disease]: A narrative review" → RT-306
- "Efficacy of [drug] in [condition]: A meta-analysis" → RT-303


### RULE 7: Supplementary Appendices

Supplementary materials should inherit the parent document's RT-ID.
If the parent is a journal article (RT-301), the appendix is also RT-301.

**Detection:** "supplementary", "appendix", "supporting information", "online supplement"
in filename or title.


### RULE 8: Patient Education vs. COA Instruments (B8 Ambiguity)

The B8 category in the taxonomy covers "Instruments, Standards & Scientific Documents"
(RT-801 = COA instrument manual, RT-802 = staging system, etc.).

Patient education booklets (disease awareness, treatment guides for patients)
do NOT perfectly fit any B8 subcategory. However, RT-801 is the closest match.

**Detection for patient education:**
- Published by a patient foundation
- Written for lay audience (no statistical methods, simple language)
- Topics: "What is [disease]?", "Living with...", "Treatment options for patients"

**Action:** Classify as RT-801 (B8) with a note in reasoning that it's patient
education material (taxonomy gap). This is an acceptable approximation.


### RULE 9: Cross-Validation Checks (Post-Classification)

After classification, verify these consistency rules:
1. If category is B2 (Clinical Trial) → document MUST contain patient numbers,
   endpoints, or trial design. If not → likely misclassified.
2. If RT-ID is RT-301 → document MUST have authors, DOI or journal name.
3. If RT-ID is RT-901 (DOF) → document MUST NOT have a DOI or journal name.
4. If category is B4 (Conference) → document should be relatively short (<30 pages).
5. If RT-ID is RT-101 (USPI) → document MUST contain FDA-mandated sections.


### RULE 10: Ambiguous Documents — Filename vs. Content Priority

When filename and content disagree:
- **Content wins** for RT-ID assignment (it's what the document actually IS)
- **Filename wins** for conference detection (body text often omits "poster")
- **Neither wins alone** for DOF — need BOTH filename AND content signals


### RULE 11: Published Clinical Trials ≠ Clinical Study Reports (CSR)

A paper published in a peer-reviewed journal that REPORTS the results of a
clinical trial is STILL a journal article (RT-301), NOT a CSR (RT-209).

**Key distinction:**
- RT-301 (journal article): Published in a journal, has DOI, has journal name,
  authors, peer review. Even if it describes an RCT with endpoints, patient
  numbers, and trial design — it's a PUBLICATION.
- RT-209 (CSR): An ICH E3-formatted internal regulatory document submitted to
  regulatory agencies. Never has a journal name or DOI. Typically hundreds of
  pages with appendices.

**Detection:** If the document has a journal name AND DOI → it is RT-301,
regardless of whether it contains trial results.

**Few-shot examples (generic):**
- "Randomized trial of [drug] vs placebo in [disease]", N Engl J Med → RT-301
  (published RCT, NOT RT-209)
- "Study ABC-1234: A Phase 3 Clinical Study Report" (no DOI, ICH E3 format) → RT-209
'''
