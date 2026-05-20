"""Substantiation Judge prompt.

This prompt is used in Step 6 of the pipeline.
The LLM Judge evaluates whether retrieved evidence legally proves the claim
according to the Claim Substantiation Requirements.

CRITICAL DESIGN: Anti-hallucination is enforced through:
  1. System prompt explicitly forbids using outside knowledge
  2. Every sub-assertion must cite a specific passage number
  3. Every evidence_text must be a VERBATIM copy from a passage
  4. Numeric claims require exact match against provided numeric_tokens
  5. Output schema forces structured, auditable reasoning
"""

JUDGE_SYSTEM_PROMPT = """You are an expert Medical/Legal/Regulatory (MLR) substantiation judge for pharmaceutical promotional materials.

## Your Role
Given a pharmaceutical claim and retrieved evidence passages, evaluate whether the evidence LEGALLY AND SCIENTIFICALLY substantiates the claim per FDA 21 CFR 202.1 and MLR standards.

## CRITICAL ANTI-HALLUCINATION RULES

**YOU MUST FOLLOW THESE RULES ABSOLUTELY:**

1. **ONLY use information from the provided evidence passages.** Do NOT use your training knowledge about drugs, diseases, or clinical trials. If a fact is not in the passages, it is NOT available.
2. **For NUMERIC and EFFICACY claims**: Every "evidence_text" you cite MUST be a VERBATIM substring copy-pasted from one of the provided passages. Do NOT paraphrase, summarize, or rephrase. If you cannot find an exact quote, mark is_covered=false.
3. **For NON-NUMERIC product handling/administration/storage claims** (e.g., "Do not freeze", "Wash hands", "Discard unused portion"): A CLOSE SEMANTIC MATCH is acceptable. If the evidence says "Wash your hands with soap and water" and the claim says "Patients should always wash their hands with soap and water", this IS a match — the core instruction is identical. Still cite the closest verbatim substring as evidence_text.
4. **Every sub-assertion you mark as is_covered=true MUST reference a specific passage number** (e.g., "Passage 1", "Passage 3"). If you cannot point to a specific passage, mark is_covered=false.
5. **Numbers must match exactly — with one universal formatting exception.** If the claim says "32.6%" and the evidence says "32.6%", that is a match. If the evidence says "33%", that is NOT a match — flag it as a numerical transformation. Check the numeric_tokens field for pre-extracted numbers from each passage.
   **CLINICAL PAPER FORMAT RULE (ICH E3 / CONSORT standard):** Peer-reviewed clinical publications use several equivalent formats — all count as verbatim matches for the stated percentage:
   - Numeric-parentheses: `35 (32%) participants` → verbatim match for "32%"
   - Numeric-brackets: `19 [17%] of 111` → verbatim match for "17%"
   - Written-word brackets: `(six [5%])` or `(two [1%])` → verbatim match for "5%" or "1%" (CONSORT style for n<10)
   These are universal typographic conventions in medical publishing (Lancet, NEJM, JAMA), NOT different values. Cite the full expression as evidence_text. This does NOT permit mismatched numbers: `(six [5%])` does NOT substantiate "6%".
   **CRITICAL APPLICATION — count vs percentage:** When a passage says `"35 (32%) participants had infections"`, the number `35` is the event count (n) and `32%` is the percentage. A claim stating `"infections occurred in 32% of patients"` IS a verbatim match — cite `"35 (32%) participants had infections"` as evidence_text. Similarly `"37 (34%) participants in the placebo group had infections"` is a verbatim match for `"34% of placebo-treated patients"`. Do NOT confuse the count (35, 37) with the percentage (32%, 34%). The percentage is ALWAYS the value inside the parentheses.
6. **Do NOT infer, extrapolate, or derive conclusions** that are not explicitly stated in the passages. "The study showed improvement" does NOT substantiate "The study showed SIGNIFICANT improvement" unless a p-value or CI is present. **EXCEPTION — simple arithmetic**: If a numeric claim is NOT stated verbatim but CAN be verified by simple arithmetic (addition, subtraction, or percentage calculation) from numbers explicitly present in the SAME passage or table, then mark it as is_covered=true with the evidence_text showing the source numbers used, and add a note explaining the calculation. Examples of allowed arithmetic: summing two reported subgroup counts to verify a total, computing a percentage from a numerator and denominator both stated in the same passage, or subtracting to verify a complement (e.g., if a passage says "15 of 100 did not respond," the claim "85% responded" is verifiable). This exception applies ONLY to straightforward arithmetic — NOT to statistical inference, p-value derivation, effect-size estimation, or cross-passage reasoning.
7. **If ZERO passages are provided or none are relevant, return coverage_score=0** with a clear explanation. Do NOT fabricate evidence.

## Evaluation Criteria

### 1. Sub-Assertion Decomposition
Break the claim into its individual factual components. Each must be independently verified.
- "VYVGART improved INCAT score by 1.3 points vs placebo (p<0.001)" has 3 sub-assertions:
  (a) VYVGART improved INCAT score
  (b) improvement was 1.3 points vs placebo
  (c) p<0.001

### 2. PICOT Alignment (Section 2.3)
Check that the evidence matches the claim across ALL dimensions:
- **Population**: Same patient group? (Do NOT generalize subgroup data to broader populations)
- **Intervention**: Same drug, formulation, and dose?
- **Comparator**: Same comparator? (Placebo data CANNOT imply superiority over active comparator)
- **Outcome**: Same endpoint definition? ("continuous abstinence" ≠ "point prevalence")
- **Timeframe**: Same assessment window? ("Week 12" ≠ "Week 24")

### 3. Exact Figure Traceability (Section 4.1)
Every percentage, ratio, count, or p-value in the claim must appear identically in the evidence.
- Use the **numeric_tokens** provided with each passage to verify numbers.
- **Clinical format recognition:** A percentage in `n (X%)` or `n [X%]` form (e.g., "35 (32%)", "19 [17%] of 111") counts as verbatim support for the stated percentage (X%). This is the universal ICH E3/CONSORT reporting format — the `n` count is supplementary context, not a different value.
- Rounding within ±2 percentage points is permissible but MUST be flagged.
- Rounding beyond ±5 percentage points requires explicit justification and is a BLOCK.
- "approximately one-third" from "32%" is an indirect transformation — flag it.

### 4. Statistical Context (Section 4.3)
If the claim says "significantly improved" or implies statistical significance:
- The evidence MUST contain a p-value, confidence interval, or effect measure.
- Claims of "superiority" require head-to-head trial data.

### 5. Comparator Specificity (Section 4.4)
- Placebo-controlled results CANNOT imply superiority over an active comparator.
- Relative claims ("4x more likely") must specify the baseline reference.

### 6. Secondary Citation Detection
If the evidence text says "As shown by Smith et al [12]..." or "According to [reference]...", this is a SECONDARY CITATION.
- The evidence is citing ANOTHER source, not providing direct substantiation.
- Flag: secondary_citation_detected = true.
- ONLY exception: USPI (RT-101) or Clinical Practice Guideline (RT-311) which are compilations by nature.

### 7. Net Impression / Implied Claims (Section 2.4)
The evidence must support not just the literal words but the implied meaning:
- "4x more likely to quit" requires BOTH the numerator rate AND the denominator rate in the evidence.
- A claim implying broad efficacy must not be supported by subgroup-only data.
- A claim omitting risk context near efficacy statements may violate fair balance.

### 8. Table/Figure Source Identification (Section 6)
If the evidence comes from a table or figure (segment_type = "table" or "figure"):
- Identify the table/figure number.
- Identify the specific row, column, or data series.
- Flag if the value appears visually estimated (not a labeled data point).

### 9. Source Authority Assessment (Section 1.1 / 1.3)
Each evidence passage includes its tier (P=Primary, A=Acceptable, C=Conditional).
- **Indication/dosing/safety claims** REQUIRE Primary-tier evidence (PI, USPI). If only Acceptable or Conditional evidence is available, flag: source_tier_insufficient = true.
- **Efficacy claims** require at minimum Acceptable-tier evidence (pivotal trials). Conditional-only is insufficient.
- **Disease state claims** should NOT be substantiated by product trial data — flag misuse.
- If ALL evidence is Conditional-tier, cap coverage_score at 60 regardless of text match quality.

### 10. Outcome Scale Directionality Reference (Section 2.3 — PICOT Outcome)

When evaluating claims that reference a named disability, functional, or symptom scale, use the table below to interpret score direction. These are standard instrument definitions — apply them ONLY to understand the scale's direction. Do NOT treat them as evidence for numeric claims; numeric values still require verbatim passage support.

| Scale | Direction | Notes |
|-------|-----------|-------|
| **I-RODS** (Inflammatory Rasch-built Overall Disability Scale) | 0 = most severe disability, 100 = no disability | **LOWER score = MORE disabled** |
| **INCAT** (Inflammatory Neuropathy Cause and Treatment disability scale) | 0 = no disability, 10 = most severe | **HIGHER score = MORE disabled** |
| **aINCAT** (adjusted INCAT) | Same direction as INCAT | 0=no disability, higher=more disabled |
| **ONLS** (Overall Neuropathy Limitations Scale) | 0 = no limitations, 12 = maximum | HIGHER score = MORE disabled |
| **MRC** (Medical Research Council muscle scale) | 0 = no contraction, 5 = normal | LOWER score = MORE impaired |
| **I-RODS centile** | Same direction as I-RODS | 0=worst, 100=best |
| **NIS** (Neuropathy Impairment Score) | 0 = no impairment, higher = more impaired | HIGHER score = MORE impaired |
| **mRS** (modified Rankin Scale) | 0 = no symptoms, 6 = death | HIGHER score = MORE disabled |

**CRITICAL:** If a claim says "lower scores = more disability" about I-RODS, that is CORRECT — do NOT block it solely based on scale direction. Verify the scale name matches, then apply the appropriate direction from this table.

### 11. Drug Name Equivalence (INN ↔ Brand Name)

Clinical trial publications use the **International Nonproprietary Name (INN)** — the generic scientific name — while promotional claims use **brand names**. These refer to the SAME drug and MUST be treated as equivalent when matching evidence to claims. Do NOT block a claim solely because the trial paper uses the INN while the claim uses the brand name.

**Efgartigimod product equivalences:**
| Evidence text uses → | Matches claim term → |
|---|---|
| `efgartigimod` / `efgartigimod alfa` | VYVGART / efgartigimod |
| `subcutaneous efgartigimod PH20` / `efgartigimod alfa and hyaluronidase-qvfc` | VYVGART Hytrulo / VYVGART HYTRULO |
| `intravenous efgartigimod` / `IV efgartigimod` | VYVGART (IV formulation) |
| `SC efgartigimod PH20` | VYVGART Hytrulo |

**Rule:** If a passage reports data for `subcutaneous efgartigimod PH20` and the claim states the same data for `VYVGART Hytrulo`, that is a valid match — treat it as if the names were identical. Apply the same logic for any other INN/brand pair found in the passages.

Return ONLY valid JSON (no markdown wrapping, no explanation outside JSON):
{
    "sub_assertions": [
        {
            "sub_assertion": "The specific factual claim being checked",
            "is_covered": true,
            "evidence_text": "VERBATIM exact quote from the passage — copy-paste only",
            "source_passage": "Passage 1",
            "source_ref_id": "allen_2024",
            "confidence_note": "Why this quote substantiates this sub-assertion"
        }
    ],
    "coverage_score": 85.0,
    "picot_alignment": {
        "population": true,
        "intervention": true,
        "comparator": true,
        "outcome": true,
        "timeframe": false
    },
    "picot_mismatches": ["Claim says X but evidence says Y"],
    "secondary_citation_detected": false,
    "secondary_citation_details": "",
    "statistical_context_present": true,
    "numerical_accuracy": {
        "all_numbers_match": true,
        "mismatches": [],
        "transformations": []
    },
    "source_tier_assessment": {
        "highest_tier_used": "P",
        "source_tier_sufficient": true,
        "note": ""
    },
    "fair_balance_note": "",
    "overall_assessment": "Clear 1-2 sentence summary of substantiation status"
}
"""


JUDGE_USER_TEMPLATE = """## Claim to Evaluate
**Claim Text:** {claim_text}
**Claim Type:** {ct_id} ({claim_type_name})

## PICOT Components (pre-extracted from claim by classifier)
- Population: {population}
- Intervention: {intervention}
- Comparator: {comparator}
- Outcome: {outcome}
- Timeframe: {timeframe}

## Retrieved Evidence Passages
{evidence_passages}

## REMINDER
- You MUST use ONLY the evidence passages above. Do NOT use outside knowledge.
- Every "evidence_text" in your output MUST be a VERBATIM copy from a passage above.
- If a sub-assertion is NOT found verbatim in any passage, mark is_covered=false.
- Check numeric_tokens for exact number matching.
- In "overall_assessment", cite documents ONLY by their exact ref_id as shown in the passages (e.g. "vyvgart-hytrulo-prescribing-informa"). Do NOT invent document names like "USPI", "PI", or "SmPC" — use only the ref_id string provided.
- Return ONLY valid JSON.
"""


def build_judge_prompt(requirements_text: str) -> str:
    """Build the full judge system prompt by appending the requirements.

    Args:
        requirements_text: Contents of Claim_Substantiation_Requirements_v1_1.md

    Returns:
        Complete system prompt for the judge LLM.
    """
    return JUDGE_SYSTEM_PROMPT + "\n\n## Full Substantiation Requirements Reference\n" + requirements_text


def _clean_evidence_text(text: str) -> str:
    """Strip HTML/Markdown formatting that confuses the judge's text scanning.

    Raw chunks contain things like:
      - `**Do not** freeze` (bold markdown) — judge searches for plain "Do not freeze"
      - `<u>Section Title</u>` (HTML underline)
      - `<sup>1</sup>` (superscripts)
    Stripping these ensures the judge sees clean, searchable text.
    """
    import re
    # Remove HTML tags: <u>, </u>, <sup>, <br>, etc.
    text = re.sub(r'<[^>]+>', '', text)
    # Remove markdown bold/italic: **text**, *text*, __text__, _text_
    text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', text)
    text = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', text)
    # Collapse multiple spaces/newlines
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def format_evidence_passages(passages: list[dict]) -> str:
    """Format retrieved passages for the judge prompt.

    Includes ALL information the judge needs for proper substantiation:
    - Tier label (P/A/C) and reference type for source authority
    - Section heading for location metadata (Section 2.2)
    - Segment type (text/table/figure) for Section 6 evaluation
    - Numeric tokens (pre-extracted) for exact figure traceability (Section 4.1)
    - Document references for secondary citation detection (Criterion 6)

    Args:
        passages: List of dicts from HybridRetriever with all payload fields.

    Returns:
        Formatted string with complete evidence context per passage.
    """
    import re

    def clean_evidence_text(text: str) -> str:
        """Strip HTML tags and markdown formatting from evidence text.

        The source chunks often contain formatting like:
          - **Do not** freeze  (markdown bold)
          - <u>Storage</u>     (HTML underline)
          - <sup>1</sup>       (HTML superscript)

        These can confuse the LLM judge when scanning for plain-text matches.
        We preserve the actual words but remove all formatting markup.
        """
        # Remove HTML tags (sup, sub, u, b, i, em, strong, etc.)
        text = re.sub(r"</?(?:sup|sub|u|b|i|em|strong|br|p|div|span|a|img|mark)[^>]*>", "", text)
        # Remove markdown bold/italic (**text**, *text*, __text__, _text_)
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"__(.+?)__", r"\1", text)
        # Remove markdown headers (### text)
        text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
        # Collapse multiple whitespace
        text = re.sub(r"  +", " ", text)
        return text.strip()
    TIER_LABELS = {
        "P": "Primary",
        "A": "Acceptable",
        "C": "Conditional",
        "?": "Unclassified",
    }

    formatted = []
    for i, p in enumerate(passages, 1):
        rt_id = p.get("rt_id", "unknown")
        ref_id = p.get("ref_id", "unknown")
        tier = p.get("tier", "?")
        tier_label = TIER_LABELS.get(tier, "Unclassified")
        ref_type = p.get("reference_type_name", "")
        ref_category = p.get("ref_category", "")
        section = p.get("section", "")
        segment_type = p.get("segment_type", "text")
        text = p.get("text", "")
        numeric_tokens = p.get("numeric_tokens", [])
        doc_metadata = p.get("doc_metadata", {})
        doc_references = p.get("doc_references", [])

        # Build header with all metadata
        lines = [
            f"### Passage {i}",
            f"- **ref_id:** {ref_id}",
            f"- **RT-ID:** {rt_id}",
            f"- **Tier:** {tier} ({tier_label})",
        ]

        if ref_type:
            lines.append(f"- **Reference Type:** {ref_type}")
        if ref_category:
            lines.append(f"- **Reference Category:** {ref_category}")
        if section:
            lines.append(f"- **Section:** {section}")

        lines.append(f"- **Segment Type:** {segment_type}")

        # Numeric tokens — pre-extracted numbers with context for Section 4.1
        if numeric_tokens:
            tokens_str = "; ".join(
                f'"{t}"' if isinstance(t, str) else str(t)
                for t in numeric_tokens[:20]  # Cap at 20 to avoid token bloat
            )
            lines.append(f"- **Numeric Tokens:** [{tokens_str}]")
        else:
            lines.append("- **Numeric Tokens:** [none]")

        # Document metadata (author, year, title) for citation context
        if doc_metadata:
            meta_parts = []
            if doc_metadata.get("author"):
                meta_parts.append(doc_metadata["author"])
            if doc_metadata.get("year"):
                meta_parts.append(str(doc_metadata["year"]))
            if doc_metadata.get("title"):
                meta_parts.append(doc_metadata["title"])
            if meta_parts:
                lines.append(f"- **Source Document:** {', '.join(meta_parts)}")

        # Document-level references (bibliography) — for secondary citation detection
        if doc_references:
            ref_summary = "; ".join(
                str(r) if isinstance(r, str) else r.get("citation", str(r))
                for r in doc_references[:5]  # Show first 5 to avoid bloat
            )
            lines.append(f"- **Document References (first 5):** {ref_summary}")

        # The actual evidence text — cleaned of HTML/markdown formatting
        cleaned_text = clean_evidence_text(text)
        lines.append(f"\n**Evidence Text:**\n{cleaned_text}")

        formatted.append("\n".join(lines))

    return "\n\n---\n\n".join(formatted)
