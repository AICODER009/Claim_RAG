"""Honest generalization test — does the skill work WITHOUT memorized examples?

This test:
1. Strips all corpus-specific examples from the skill
2. Tests on docs that are NOT named in any rule
3. Tests the RULES, not the examples
"""

import sys, os, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\revisto_evidence_aligned_clean")

from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field
from openai import OpenAI

class TypizationResponse(BaseModel):
    reasoning: str
    rt_id: str
    category: Literal["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9"]
    reference_type_name: str
    confidence: float = Field(ge=0.0, le=1.0)

# Build prompt with CLEANED skill (no corpus-specific examples)
TAXONOMY_PATH = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\prompts\Reference_Document_Types.md")
taxonomy_text = TAXONOMY_PATH.read_text(encoding="utf-8")

from new_pipeline.prompts.typization_prompt import TYPIZATION_SYSTEM_PROMPT
from new_pipeline.skills.typization_skill import TYPIZATION_SKILL

# STRIP all "Example from corpus:" blocks and specific file mentions
cleaned_skill = TYPIZATION_SKILL
# Remove **Example from corpus:** blocks (2-3 lines each)
cleaned_skill = re.sub(
    r"\*\*Example from corpus:\*\*\n(- .+\n)+",
    "",
    cleaned_skill,
)
# Remove any mention of specific filenames we know
for name in ["Van den Bergh", "CTEP", "Hughes R 2001", "Allen Supplementary",
             "VYVGART", "Argenx BVBA", "Hargraves"]:
    cleaned_skill = re.sub(rf".*{re.escape(name)}.*\n?", "", cleaned_skill)

system_prompt = TYPIZATION_SYSTEM_PROMPT + "\n" + taxonomy_text + "\n" + cleaned_skill

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
MODEL = "gpt-4o-mini"
PARSED_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\LLamaParser")

# Test on docs that have TRICKY classifications but are NOT named in any rule
# These are the real generalization tests
TEST_CASES = [
    # Guideline test (Rule 1) — NOT Van den Bergh
    # Mehndiratta 2015 is a Cochrane systematic review, should be RT-302
    ("Mehndiratta et al. 2015.md", "RT-302", "B3", "Cochrane Review (not named in skill)"),

    # Journal article that reports a trial (Rule 11) — NOT Hughes
    # Gorson 2003 is a published trial in Neurology journal
    ("Gorson 2003.md", "RT-301", "B3", "Published trial (not named in skill)"),

    # Conference poster (Rule 3) — NOT Hargraves
    ("Allen JA AAN 2025.md", "RT-402", "B4", "AAN poster (not named in skill)"),

    # DOF (Rule 4) — NOT any named DOF
    ("DOF_EFG-HF-PFS-gMG-2342 and CIDP-2401 Human Factor Studies_January 2025.md",
     "RT-901", "B9", "DOF (not named in skill)"),

    # PI (Rule 5) — NOT VYVGART
    ("hizentra-prescribing-information.md", "RT-101", "B1", "PI (not named in skill)"),

    # Education (Rule 8) — use a foundation booklet not named anywhere
    ("CIDP - GBS _ CIDP Organisation Europe.md", "RT-801", "B8", "Education (not named in skill)"),

    # Supplementary appendix (Rule 7)
    ("Allen Supplementary APPENDIX_FINAL_02Sep2024.md", "RT-301", "B3", "Appendix (Rule 7)"),

    # Narrative review vs systematic review (Rule 6)
    ("Querol_Neurotherapeutics_2021.md", "RT-301", "B3", "Journal article (control)"),
]

print("=" * 70)
print("GENERALIZATION TEST — Skill with examples REMOVED")
print(f"  Prompt length: {len(system_prompt)} chars")
print("=" * 70)

passed = 0
total = 0
for fname, expected_rt, expected_cat, desc in TEST_CASES:
    fpath = PARSED_DIR / fname
    if not fpath.exists():
        print(f"\n  SKIP: {fname}")
        continue

    md = fpath.read_text(encoding="utf-8")
    user_msg = f"## Document Filename\n{fname}\n\n## Document Text (First Pages)\n{md[:8000]}"

    try:
        response = client.beta.chat.completions.parse(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.1,
            response_format=TypizationResponse,
        )
        p = response.choices[0].message.parsed

        match = p.rt_id == expected_rt and p.category == expected_cat
        emoji = "OK" if match else "XX"
        if match:
            passed += 1
        total += 1

        print(f"\n  [{emoji}] {desc}")
        print(f"       Got:      {p.rt_id} ({p.category}) — {p.reference_type_name}")
        print(f"       Expected: {expected_rt} ({expected_cat})")
        print(f"       Reasoning: {p.reasoning[:120]}...")

    except Exception as e:
        print(f"\n  [!!] {desc}: ERROR — {e}")
        total += 1

print(f"\n{'='*70}")
print(f"GENERALIZATION: {passed}/{total} passed (without memorized examples)")
print("=" * 70)
