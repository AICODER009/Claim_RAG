"""Re-typize all 86 docs WITH the expert skill, then compare against the old registry."""

import sys, os, json, time
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

from new_pipeline.prompts.typization_prompt import TYPIZATION_SYSTEM_PROMPT
from new_pipeline.skills.typization_skill import TYPIZATION_SKILL
system_prompt = TYPIZATION_SYSTEM_PROMPT + "\n" + taxonomy_text + "\n" + TYPIZATION_SKILL

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
MODEL = "gpt-4o-mini"

PARSED_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\LLamaParser")
OLD_REG_PATH = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\typization_registry.json")
NEW_REG_PATH = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\typization_registry_with_skill.json")

# Load old registry for comparison
old_reg = json.loads(OLD_REG_PATH.read_text(encoding="utf-8"))

# Resume support
if NEW_REG_PATH.exists():
    new_reg = json.loads(NEW_REG_PATH.read_text(encoding="utf-8"))
    print(f"Resuming: {len(new_reg)} already done")
else:
    new_reg = {}

md_files = sorted(PARSED_DIR.glob("*.md"))
remaining = [f for f in md_files if f.stem not in new_reg]
print(f"Total: {len(md_files)} | Done: {len(new_reg)} | Remaining: {len(remaining)}")
print(f"Prompt: {len(system_prompt)} chars (with skill)")
print("=" * 70)

for i, fpath in enumerate(remaining):
    fname = fpath.stem
    md = fpath.read_text(encoding="utf-8")
    user_msg = f"## Document Filename\n{fpath.name}\n\n## Document Text (First Pages)\n{md[:8000]}"

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
        new_reg[fname] = {
            "rt_id": p.rt_id,
            "category": p.category,
            "reference_type_name": p.reference_type_name,
            "confidence": p.confidence,
            "reasoning": p.reasoning,
        }

        # Check if changed from old
        old = old_reg.get(fname, {})
        old_rt = old.get("rt_id", "???")
        changed = old_rt != p.rt_id
        marker = " ** CHANGED **" if changed else ""
        print(f"  [{i+1:2d}/{len(remaining)}] {fname[:50]:50s} {p.rt_id} ({p.category}){marker}")
        if changed:
            print(f"           OLD: {old_rt} -> NEW: {p.rt_id} ({p.reference_type_name})")

    except Exception as e:
        print(f"  [{i+1:2d}/{len(remaining)}] {fname[:50]:50s} ERROR: {e}")

    if (i + 1) % 10 == 0:
        NEW_REG_PATH.write_text(json.dumps(new_reg, indent=2, ensure_ascii=False), encoding="utf-8")

# Final save
NEW_REG_PATH.write_text(json.dumps(new_reg, indent=2, ensure_ascii=False), encoding="utf-8")

# Comparison summary
print("\n" + "=" * 70)
print("COMPARISON: Old (no skill) vs New (with skill)")
print("=" * 70)

changes = []
for name in sorted(new_reg.keys()):
    old = old_reg.get(name, {})
    new = new_reg[name]
    if old.get("rt_id") != new["rt_id"]:
        changes.append((name, old.get("rt_id", "???"), old.get("category", "?"),
                        new["rt_id"], new["category"], new["reference_type_name"]))

if changes:
    print(f"\n  {len(changes)} documents CHANGED classification:\n")
    for name, old_rt, old_cat, new_rt, new_cat, new_name in changes:
        print(f"  {name[:55]}")
        print(f"    OLD: {old_rt} ({old_cat})")
        print(f"    NEW: {new_rt} ({new_cat}) — {new_name}")
        print()
else:
    print("\n  No changes — all classifications identical.")

# Category distribution
cat_dist = {}
for v in new_reg.values():
    c = v["category"]
    cat_dist[c] = cat_dist.get(c, 0) + 1
print("Updated distribution:")
for cat in sorted(cat_dist.keys()):
    print(f"  {cat}: {cat_dist[cat]} docs")
print(f"  Total: {sum(cat_dist.values())}")
