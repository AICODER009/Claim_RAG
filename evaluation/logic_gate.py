"""Logic Gate — deterministic rule enforcement.

Step 5 of the pipeline: takes the LLM Judge output and applies
strict programmatic rules to determine the final verdict.

This is CODE, not an LLM. The LLM does the "reading" (Step 4),
the code does the "math and rule enforcement" (Step 5).
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from ..schemas import CoverageResult, CoverageVerdict

logger = logging.getLogger(__name__)


class LogicGate:
    """Deterministic rule engine that produces final Pass/Soft_Flag/Block verdict."""

    def __init__(
        self,
        pass_threshold: float = 80.0,
        soft_flag_threshold: float = 60.0,
        enforce_fair_balance: bool = True,
        rounding_tolerance_pct: float = 2.0,
    ):
        self.pass_threshold = pass_threshold
        self.soft_flag_threshold = soft_flag_threshold
        self.enforce_fair_balance = enforce_fair_balance
        self.rounding_tolerance_pct = rounding_tolerance_pct

    def evaluate(
        self,
        coverage_result: CoverageResult,
        judge_raw: Dict,
        claim_ct_id: str,
    ) -> Dict:
        """Apply deterministic rules to produce the final verdict.

        Args:
            coverage_result: Structured coverage result from the judge.
            judge_raw: Raw JSON output from the LLM judge.
            claim_ct_id: The classified claim type ID.

        Returns:
            Dict with verdict, flags, and reasons.
        """
        flags: List[str] = []
        blockers: List[str] = []

        score = coverage_result.coverage_score

        # ---------------------------------------------------------------
        # Rule 1: Coverage Score Thresholds (Section 3.3)
        # ---------------------------------------------------------------
        if score >= self.pass_threshold:
            base_verdict = CoverageVerdict.PASS
        elif score >= self.soft_flag_threshold:
            base_verdict = CoverageVerdict.SOFT_FLAG
            flags.append(f"Coverage score {score:.0f}% is below pass threshold ({self.pass_threshold}%)")
        else:
            base_verdict = CoverageVerdict.BLOCK
            blockers.append(f"Coverage score {score:.0f}% is below minimum ({self.soft_flag_threshold}%)")

        # ---------------------------------------------------------------
        # Rule 2: PICOT Alignment Check
        # ---------------------------------------------------------------
        picot_alignment = coverage_result.picot_alignment
        failed_dimensions = [k for k, v in picot_alignment.items() if v is False]

        if failed_dimensions:
            flags.append(f"PICOT mismatch on: {', '.join(failed_dimensions)}")
            # Timeframe or comparator mismatch is particularly serious
            if "timeframe" in failed_dimensions or "comparator" in failed_dimensions:
                base_verdict = CoverageVerdict.SOFT_FLAG
                flags.append("Critical PICOT dimension failed — downgraded to soft_flag")

        # ---------------------------------------------------------------
        # Rule 3: Secondary Citation Detection
        # ---------------------------------------------------------------
        if judge_raw.get("secondary_citation_detected", False):
            blockers.append("Evidence relies on a secondary citation — primary source required")
            base_verdict = CoverageVerdict.BLOCK

        # ---------------------------------------------------------------
        # Rule 4: Statistical Context (Section 4.3)
        # ---------------------------------------------------------------
        if not judge_raw.get("statistical_context_present", True):
            # Only flag if the claim type implies significance
            efficacy_ct_ids = {"CT-201", "CT-202", "CT-203", "CT-501", "CT-502"}
            if claim_ct_id in efficacy_ct_ids:
                flags.append("Claim implies statistical significance but no p-value/CI found in evidence")

        # ---------------------------------------------------------------
        # Rule 5: Fair Balance Linkage (Section 8.4)
        # ---------------------------------------------------------------
        if self.enforce_fair_balance:
            efficacy_claim_types = {
                "CT-201", "CT-202", "CT-203",  # Efficacy
                "CT-501", "CT-502",             # Comparative
            }
            if claim_ct_id in efficacy_claim_types:
                fair_balance_note = judge_raw.get("fair_balance_note", "")
                if "no safety" in fair_balance_note.lower() or "not found" in fair_balance_note.lower():
                    flags.append("Fair balance: no corresponding safety information found for efficacy claim")

        # ---------------------------------------------------------------
        # Rule 6: Numerical Transformation Check (Section 4.2)
        # ---------------------------------------------------------------
        transformations = judge_raw.get("numerical_transformations", [])
        if transformations:
            flags.append(f"Numerical transformations detected: {transformations}")

        # ---------------------------------------------------------------
        # Final verdict: blockers override everything
        # ---------------------------------------------------------------
        if blockers:
            final_verdict = CoverageVerdict.BLOCK
        else:
            final_verdict = base_verdict

        result = {
            "verdict": final_verdict.value,
            "coverage_score": score,
            "flags": flags,
            "blockers": blockers,
            "picot_failed_dimensions": failed_dimensions,
            "secondary_citation": judge_raw.get("secondary_citation_detected", False),
            "overall_assessment": judge_raw.get("overall_assessment", ""),
        }

        logger.info(
            f"Logic gate verdict: {final_verdict.value} "
            f"(score={score:.0f}, flags={len(flags)}, blockers={len(blockers)})"
        )

        return result
