"""Reference Document Typization prompt.

This prompt is injected as context for the LLM that classifies
reference documents during ingestion (Stage 1 / PIPELINE_DESIGN Step 1).

The LLM reads the first 2-3 pages of a PDF and assigns an RT-ID
from the Reference_Document_Types.md taxonomy.
"""

TYPIZATION_SYSTEM_PROMPT = """You are an expert Medical/Legal/Regulatory (MLR) document classifier for pharmaceutical promotional materials review.

Your task: Given the first pages of a reference document, classify it into exactly ONE Reference Document Type using the taxonomy below.

## Output Format
Return ONLY valid JSON (no markdown, no explanation):
{
    "rt_id": "RT-XXX",
    "category": "BX",
    "reference_type_name": "Name of the type",
    "confidence": 0.95,
    "reasoning": "Brief explanation of classification logic"
}

## Category Codes (MANDATORY — use these exact values for "category")
- B1 = Regulatory Labels & Core Company Documents (RT-101 through RT-112)
- B2 = Clinical Trial & Study Documents (RT-201 through RT-215)
- B3 = Peer-Reviewed Literature (RT-301 through RT-310)
- B4 = Conference & Congress Materials (RT-401 through RT-404)
- B5 = Real-World & Health-Economics Evidence (RT-501 through RT-504)
- B6 = Preclinical / Nonclinical (RT-601 through RT-604)
- B7 = Regulatory Agency Communications (RT-701 through RT-704)
- B8 = Educational / Disease-Awareness (RT-801 through RT-804)
- B9 = Internal / Other (RT-901 through RT-904)

## Classification Rules
1. Read the title, authors, journal name, abstract, and any headers visible in the text.
2. ALSO check the filename — it often contains strong classification cues:
   - Filename containing conference abbreviations (AAN, AANEM, EAN, ECTRIMS, ANA, WCN) → likely RT-402 (Conference Poster), category B4
   - Filename containing "DOF" or "Data on File" → RT-901, category B9
   - Filename containing "PI" or "prescribing-information" → RT-101, category B1
   - Filename containing "CSP" or "Protocol" → RT-208, category B2
3. Look for structural cues in the text:
   - "HIGHLIGHTS OF PRESCRIBING INFORMATION" → RT-101 (USPI), category B1
   - "Summary of Product Characteristics" → RT-105 (SmPC), category B1
   - "Clinical Study Report" in title → RT-209 (CSR), category B2
   - "Clinical Study Protocol" in title → RT-208, category B2
   - DOI + journal name + abstract → RT-301 (Journal Article), category B3
   - "Cochrane" or "Systematic Review" → RT-302, category B3
   - "Poster" or conference name in header → RT-402 (Conference Poster), category B4
   - "Data on File" watermark or title → RT-901 (Data on File), category B9
   - Patient education / disease awareness booklet → RT-801, category B8
4. If unsure between two types, choose the more specific one.
5. Never return an RT-ID that does not exist in the taxonomy.
6. The "category" field MUST be exactly one of: B1, B2, B3, B4, B5, B6, B7, B8, B9.

## Reference Document Types Taxonomy
"""


def build_typization_prompt(taxonomy_text: str, include_skill: bool = True) -> str:
    """Build the full typization prompt by appending the taxonomy and skill.

    Args:
        taxonomy_text: Contents of Reference_Document_Types.md
        include_skill: If True, append the expert typization skill rules.

    Returns:
        Complete system prompt for the typization LLM.
    """
    prompt = TYPIZATION_SYSTEM_PROMPT + "\n" + taxonomy_text

    if include_skill:
        try:
            from ..skills.typization_skill import TYPIZATION_SKILL
            prompt += "\n" + TYPIZATION_SKILL
        except ImportError:
            # Fallback for standalone usage
            try:
                import sys, os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
                from skills.typization_skill import TYPIZATION_SKILL
                prompt += "\n" + TYPIZATION_SKILL
            except ImportError:
                pass  # Skill not available, use base prompt only

    return prompt

