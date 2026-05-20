"""Substantiation Judge — LLM evaluator for claim-evidence pairs.

Step 4 of the pipeline: takes retrieved evidence passages and evaluates
whether they legally and scientifically substantiate the claim.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from ..schemas import (
    ClaimClassification,
    CoverageResult,
    PICOTComponents,
    SubAssertionResult,
)
from ..prompts.judge_prompt import (
    JUDGE_USER_TEMPLATE,
    build_judge_prompt,
    format_evidence_passages,
)

logger = logging.getLogger(__name__)


class SubstantiationJudge:
    """LLM-based judge that evaluates evidence against claims."""

    def __init__(
        self,
        api_key: str = "",
        model: str = "claude-sonnet-4-20250514",
        requirements_path: Optional[Path] = None,
    ):
        self.model = model
        self.api_key = api_key

        # Load requirements for prompt context
        if requirements_path and requirements_path.exists():
            requirements_text = requirements_path.read_text(encoding="utf-8")
        else:
            requirements_text = ""
            logger.warning("No substantiation requirements file found")

        self._system_prompt = build_judge_prompt(requirements_text)

        # Judge always uses Claude (highest quality reasoning)
        import anthropic
        self._client = anthropic.Anthropic(api_key=api_key)

    def evaluate(
        self,
        claim_text: str,
        classification: ClaimClassification,
        picot: PICOTComponents,
        evidence_passages: List[Dict],
    ) -> Dict:
        """Evaluate whether evidence substantiates the claim.

        Args:
            claim_text: The original claim text.
            classification: CT-ID classification result.
            picot: PICOT components extracted from the claim.
            evidence_passages: Retrieved passages with metadata.

        Returns:
            Raw judge output dict with coverage score, PICOT alignment, etc.
        """
        # Format the user message
        user_message = JUDGE_USER_TEMPLATE.format(
            claim_text=claim_text,
            ct_id=classification.ct_id,
            claim_type_name=classification.claim_type_name,
            population=picot.population or "Not specified",
            intervention=picot.intervention or "Not specified",
            comparator=picot.comparator or "Not specified",
            outcome=picot.outcome or "Not specified",
            timeframe=picot.timeframe or "Not specified",
            evidence_passages=format_evidence_passages(evidence_passages),
        )

        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=4000,
                system=self._system_prompt,
                messages=[{"role": "user", "content": user_message}],
                temperature=0,  # deterministic: same evidence = same verdict every run
            )
            result_text = response.content[0].text

            # Parse JSON from response (handle potential markdown wrapping)
            result_text = result_text.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]

            result = json.loads(result_text)
            logger.info(f"Judge evaluation complete: coverage={result.get('coverage_score', '?')}")
            return result

        except Exception as e:
            logger.error(f"Judge evaluation failed: {e}")
            return {
                "sub_assertions": [],
                "coverage_score": 0.0,
                "picot_alignment": {},
                "secondary_citation_detected": False,
                "statistical_context_present": False,
                "overall_assessment": f"Evaluation failed: {str(e)}",
            }

    def evaluate_to_coverage_result(
        self,
        claim_text: str,
        classification: ClaimClassification,
        picot: PICOTComponents,
        evidence_passages: List[Dict],
    ) -> CoverageResult:
        """Evaluate and return a structured CoverageResult.

        Convenience wrapper that converts the raw judge output
        into the Pydantic CoverageResult schema.
        """
        raw = self.evaluate(claim_text, classification, picot, evidence_passages)

        sub_assertions = [
            SubAssertionResult(
                sub_assertion=sa.get("sub_assertion", ""),
                is_covered=sa.get("is_covered", False),
                verbatim_anchor=sa.get("evidence_text"),
            )
            for sa in raw.get("sub_assertions", [])
        ]

        return CoverageResult(
            claim_text=claim_text,
            sub_assertions=sub_assertions,
            coverage_score=raw.get("coverage_score", 0.0),
            picot=picot,
            picot_alignment=raw.get("picot_alignment", {}),
        )
