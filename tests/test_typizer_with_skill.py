"""Test typization WITH the skill on previously misclassified docs."""

import sys, os
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

# Build prompt WITH skill
TAXONOMY_PATH = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\prompts\Reference_Document_Types.md")
taxonomy_text = TAXONOMY_PATH.read_text(encoding="utf-8")

# Manual skill injection (since relative imports won't work in standalone script)
from new_pipeline.prompts.typization_prompt import TYPIZATION_SYSTEM_PROMPT
from new_pipeline.skills.typization_skill import TYPIZATION_SKILL
system_prompt = TYPIZATION_SYSTEM_PROMPT + "\n" + taxonomy_text + "\n" + TYPIZATION_SKILL

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
MODEL = "gpt-4o-mini"
PARSED_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\LLamaParser")

# Test the two previously misclassified docs
TEST_CASES = [
    ("Van den Bergh_Eur J Neurol_2021.md", "RT-311", "B3", "EAN/PNS Guideline"),
    ("CTEP Trial Development and Conduct - NCI.md", "RT-311", "B3", "Methodology Guide"),
    # Also test a regular journal article to make sure skill doesn't over-correct
    ("Al-zuhairy 2021.md", "RT-301", "B3", "Journal Article (control)"),
    # And a poster
    ("Hargraves AAN 2025.md", "RT-402", "B4", "Poster (control)"),
]

print("=" * 70)
print(f"TYPIZATION WITH SKILL — Model: {MODEL}")
print(f"  Prompt length: {len(system_prompt)} chars")
print("=" * 70)

for fname, expected_rt, expected_cat, dtype in TEST_CASES:
    fpath = PARSED_DIR / fname
    if not fpath.exists():
        print(f"\n  SKIP: {fname}")
        continue

    md = fpath.read_text(encoding="utf-8")
    user_msg = f"## Document Filename\n{fname}\n\n## Document Text (First Pages)\n{md[:8000]}"

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
    print(f"\n  [{emoji}] {dtype:25s}: {p.rt_id} ({p.category}) — {p.reference_type_name}")
    print(f"       Expected: {expected_rt} ({expected_cat})")
    print(f"       Reasoning: {p.reasoning[:150]}...")

print(f"\n{'='*70}")
print("DONE")
