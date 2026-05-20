"""Test the Typizer with structured outputs (constrained decoding).

This validates that:
1. The model returns valid B1-B9 category codes (enforced by Literal type)
2. The reasoning field is populated (chain-of-thought)
3. All 6 document types classify correctly
"""

import sys, os, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\revisto_evidence_aligned_clean")

from pathlib import Path
from pydantic import BaseModel, Field
from typing import Literal

# Use the inline schema for testing (matches typizer.py)
class TypizationResponse(BaseModel):
    reasoning: str
    rt_id: str
    category: Literal["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9"]
    reference_type_name: str
    confidence: float = Field(ge=0.0, le=1.0)

from openai import OpenAI

TAXONOMY_PATH = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\prompts\Reference_Document_Types.md")
sys.path.insert(0, r"D:\revisto_evidence_aligned_clean\new_pipeline\prompts")
from typization_prompt import build_typization_prompt

taxonomy_text = TAXONOMY_PATH.read_text(encoding="utf-8") if TAXONOMY_PATH.exists() else ""
system_prompt = build_typization_prompt(taxonomy_text)

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
MODEL = "gpt-4o-mini"

PARSED_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\LLamaParser")

TEST_CASES = [
    ("vyvgart-hytrulo-prescribing-information_3.26.md", "RT-10", "B1", "Prescribing Info"),
    ("ARGX-113-1902 - ADHERE+ Clinical Study Protocol Version 8 - 02 Jul 2024.md", "RT-20", "B2", "Clinical Protocol"),
    ("Hargraves AAN 2025.md", "RT-40", "B4", "Conference Poster"),
    ("REF-04130_DOF_ADHERE IA2+_May 2025.md", "RT-90", "B9", "Data on File"),
    ("Hughes_Cochrane Database Syst Rev_2017.md", "RT-30", "B3", "Cochrane/Journal"),
    ("GBS CIDP Foundation Education-Booklet.md", "RT-80", "B8", "Education"),
]

print("=" * 70)
print(f"TYPIZER TEST — Structured Outputs — Model: {MODEL}")
print("=" * 70)

results = []
for fname, expected_rt, expected_cat, dtype in TEST_CASES:
    fpath = PARSED_DIR / fname
    if not fpath.exists():
        print(f"\n  SKIP: {fname} not found")
        continue

    md = fpath.read_text(encoding="utf-8")
    user_msg = f"## Document Filename\n{fname}\n\n## Document Text (First Pages)\n{md[:8000]}"

    try:
        # Use structured outputs with parse()
        response = client.beta.chat.completions.parse(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.1,
            response_format=TypizationResponse,
        )
        parsed = response.choices[0].message.parsed

        rt_ok = parsed.rt_id.startswith(expected_rt)
        cat_ok = parsed.category == expected_cat
        status = "PASS" if (rt_ok and cat_ok) else "FAIL"
        emoji = "OK" if status == "PASS" else "XX"

        print(f"\n  [{emoji}] {dtype:20s}: {parsed.rt_id} ({parsed.category}) — {parsed.reference_type_name}")
        print(f"       Expected: {expected_rt}x ({expected_cat})")
        print(f"       Confidence: {parsed.confidence:.2f}")
        print(f"       Reasoning: {parsed.reasoning[:100]}...")
        
        results.append({"dtype": dtype, "status": status})

    except Exception as e:
        print(f"\n  [!!] {dtype}: ERROR — {e}")
        results.append({"dtype": dtype, "status": "ERROR"})

print(f"\n{'='*70}")
passed = sum(1 for r in results if r["status"] == "PASS")
print(f"RESULTS: {passed}/{len(results)} passed (with structured outputs)")
print("=" * 70)
