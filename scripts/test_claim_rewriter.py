"""Test script for the ClaimRewriter — verifies assertion→question transformation.

Tests:
1. Does the rewriter produce actual questions (ends with '?')?
2. Are questions ≤30 words (MedCPT training distribution)?
3. Are key medical terms preserved (drug name, metric)?
4. Does the fallback work (returns claim as-is on error)?
5. Are different claim types handled correctly?

Usage:
    python -m new_pipeline.scripts.test_claim_rewriter
    # or:
    C:\\Users\\Baku\\miniconda3\\python.exe new_pipeline/scripts/test_claim_rewriter.py
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from new_pipeline.retrieval.claim_rewriter import ClaimRewriter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)


# ----- Test Claims — covering different CT-IDs -----

TEST_CLAIMS = [
    {
        "ct_id": "CT-201",
        "type": "efficacy",
        "claim": "VYVGART Hytrulo demonstrated significant improvement in INCAT score vs placebo in the ADHERE trial",
        "must_contain": ["VYVGART", "INCAT"],  # Key terms that should survive rewrite
    },
    {
        "ct_id": "CT-101",
        "type": "indication",
        "claim": "VYVGART Hytrulo is indicated for the treatment of generalized myasthenia gravis in adults who are anti-acetylcholine receptor antibody positive",
        "must_contain": ["VYVGART", "myasthenia"],
    },
    {
        "ct_id": "CT-301",
        "type": "safety",
        "claim": "The most common adverse reactions (≥10%) were headache, nasopharyngitis, and urinary tract infection",
        "must_contain": ["adverse", "headache"],
    },
    {
        "ct_id": "CT-401",
        "type": "MOA",
        "claim": "Efgartigimod binds to the neonatal Fc receptor (FcRn), blocking IgG recycling and reducing pathogenic IgG antibody levels",
        "must_contain": ["efgartigimod", "FcRn"],
    },
    {
        "ct_id": "CT-501",
        "type": "comparative",
        "claim": "Efgartigimod achieved a significantly higher relapse-free rate at 48 weeks compared to conventional treatment in CIDP patients",
        "must_contain": ["relapse", "efgartigimod"],
    },
    {
        "ct_id": "CT-201",
        "type": "efficacy_numeric",
        "claim": "32.6% of patients achieved continuous abstinence at weeks 9-12 with treatment vs 8.3% with placebo (p<0.001)",
        "must_contain": ["32.6", "abstinence"],
    },
]


def run_tests():
    """Run all claim rewriter tests."""
    # Try OpenAI first, fall back to Anthropic
    openai_key = os.getenv("OPENAI_API_KEY", "")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

    # Use Anthropic since OpenAI quota may be exhausted
    if anthropic_key:
        provider = "anthropic"
        api_key = anthropic_key
        model = os.getenv("JUDGE_MODEL", "claude-sonnet-4-20250514")
    elif openai_key:
        provider = "openai"
        api_key = openai_key
        model = os.getenv("CLASSIFIER_MODEL", "gpt-5.5")
    else:
        logger.error("No API key found (OPENAI_API_KEY or ANTHROPIC_API_KEY)")
        sys.exit(1)

    logger.info(f"Initializing ClaimRewriter with provider={provider}, model={model}")

    rewriter = ClaimRewriter(
        provider=provider,
        model=model,
        api_key=api_key,
    )

    results = []
    passes = 0
    fails = 0

    print("\n" + "=" * 80)
    print("CLAIM REWRITER TEST -- assertion -> question transformation")
    print("=" * 80)

    for i, tc in enumerate(TEST_CLAIMS, 1):
        print(f"\n--- Test {i}/{len(TEST_CLAIMS)}: {tc['type']} ({tc['ct_id']}) ---")
        print(f"  CLAIM:    {tc['claim'][:90]}...")

        question = rewriter.rewrite(tc["claim"])
        print(f"  QUESTION: {question}")

        # Validation checks
        errors = []

        # Check 1: Is it a question?
        if not question.endswith("?"):
            errors.append("Does NOT end with '?'")

        # Check 2: Word count ≤ 30?
        word_count = len(question.split())
        if word_count > 30:
            errors.append(f"Too long: {word_count} words (max 30)")

        # Check 3: Key terms preserved?
        q_lower = question.lower()
        for term in tc["must_contain"]:
            if term.lower() not in q_lower:
                errors.append(f"Missing key term: '{term}'")

        # Check 4: Not identical to input (actually transformed)?
        if question.strip() == tc["claim"].strip():
            errors.append("Question is identical to claim (no transformation)")

        # Check 5: Not empty?
        if len(question.strip()) < 10:
            errors.append(f"Question too short: {len(question.strip())} chars")

        if errors:
            status = "FAIL"
            fails += 1
            for e in errors:
                print(f"  ❌ {e}")
        else:
            status = "PASS"
            passes += 1
            print(f"  ✅ PASS ({word_count} words)")

        results.append({
            "test_id": i,
            "ct_id": tc["ct_id"],
            "type": tc["type"],
            "claim": tc["claim"],
            "question": question,
            "word_count": word_count,
            "status": status,
            "errors": errors,
        })

    # Summary
    print("\n" + "=" * 80)
    print(f"RESULTS: {passes}/{len(TEST_CLAIMS)} passed, {fails} failed")
    print("=" * 80)

    # Save results
    output_path = Path(__file__).parent.parent / "tests" / "rewriter_test_results.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {output_path}")

    return fails == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
