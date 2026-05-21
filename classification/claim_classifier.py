"""Claim Classifier — assigns CT-ID and extracts PICOT.

Stage 2 / Step 1 of the pipeline: a single LLM call that:
  1. Classifies the claim into a CT-ID
  2. Extracts PICOT components for downstream evaluation

Aligned with categorization_new/ (pre-2026-05-20):
  - Populates claim_group, audience_constraint, is_modifier_only,
    is_study_design, mapping_pending from MappingMatrix constants.
  - CT-D01–CT-D06 (A11 Study Design) supported; mapping_pending=True.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional, Tuple

from ..schemas import ClaimClassification, PICOTComponents, AudienceConstraint
from ..prompts.classification_prompt import build_classification_prompt
from ..retrieval.mapping_matrix import MappingMatrix

logger = logging.getLogger(__name__)


# Mapping from CT-ID prefix/range to claim_group A-code
_CT_GROUP_MAP: dict = {
    "CT-10": "A1", "CT-11": "A1",
    "CT-20": "A2",
    "CT-30": "A3", "CT-31": "A3",
    "CT-40": "A4",
    "CT-50": "A5",
    "CT-60": "A6",
    "CT-70": "A7",
    "CT-80": "A7",
    "CT-801": "A8", "CT-802": "A8", "CT-803": "A8",
    "CT-804": "A8", "CT-805": "A8", "CT-806": "A8", "CT-807": "A8",
    "CT-90": "A9",
    "CT-B0": "A10",
    "CT-A0": "A10",   # evidence-type modifiers — still grouped with A10 context
    "CT-D0": "A11",
}


def _infer_claim_group(ct_id: str) -> Optional[str]:
    """Infer the A-group from a CT-ID string."""
    for prefix, group in _CT_GROUP_MAP.items():
        if ct_id.startswith(prefix):
            return group
    # Single-digit suffix fallback
    if ct_id.startswith("CT-9"):
        return "A9"
    if ct_id.startswith("CT-7"):
        return "A7"
    return None


class ClaimClassifier:
    """Classify pharmaceutical claims into CT-IDs and extract PICOT."""

    MAX_RETRIES = 3

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-5.5",
        api_key: str = "",
        taxonomy_path: Optional[Path] = None,
    ):
        self.provider = provider
        self.model = model
        self.api_key = api_key

        # Load the claim taxonomy for prompt context
        if taxonomy_path and taxonomy_path.exists():
            self._taxonomy_text = taxonomy_path.read_text(encoding="utf-8")
        else:
            self._taxonomy_text = ""
            logger.warning("No claim taxonomy file found")

        self._system_prompt = build_classification_prompt(self._taxonomy_text)

        # Initialize LLM client
        if provider == "openai":
            from openai import OpenAI
            self._client = OpenAI(api_key=api_key)
        elif provider == "anthropic":
            import anthropic
            self._client = anthropic.Anthropic(api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def classify(self, claim_text: str) -> Tuple[ClaimClassification, PICOTComponents]:
        """Classify a claim and extract its PICOT components.

        Args:
            claim_text: The pharmaceutical marketing claim.

        Returns:
            Tuple of (ClaimClassification, PICOTComponents).
        """
        try:
            if self.provider == "openai":
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self._system_prompt},
                        {"role": "user", "content": claim_text},
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"},
                )
                result_text = response.choices[0].message.content

            elif self.provider == "anthropic":
                response = self._client.messages.create(
                    model=self.model,
                    max_tokens=800,
                    system=self._system_prompt + "\n\nIMPORTANT: Respond with ONLY valid JSON, no markdown, no explanation.",
                    messages=[{"role": "user", "content": claim_text}],
                    temperature=0.1,
                )
                result_text = response.content[0].text

            # Parse JSON — handle cases where LLM wraps in markdown or adds text
            result_text = result_text.strip()
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', result_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise ValueError(f"No JSON found in response: {result_text[:200]}")

            picot_data = result.get("picot", {})
            ct_id = result["ct_id"]

            # ── Derive metadata from MappingMatrix class constants ──────────
            is_modifier = ct_id in MappingMatrix.MODIFIER_CT_IDS
            is_study_design = ct_id in MappingMatrix.PENDING_MAPPING_CT_IDS
            mapping_pending = is_study_design

            # Audience — LLM may populate, or fall back to our constants
            llm_audience = result.get("audience_constraint", "unrestricted")
            if ct_id in MappingMatrix.PAYER_ONLY_CT_IDS:
                audience = AudienceConstraint.PAYER_ONLY
            elif ct_id in MappingMatrix.HCP_ONLY_CT_IDS:
                audience = AudienceConstraint.HCP_ONLY
            elif llm_audience == "payer_only":
                audience = AudienceConstraint.PAYER_ONLY
            elif llm_audience == "hcp_only":
                audience = AudienceConstraint.HCP_ONLY
            else:
                audience = AudienceConstraint.UNRESTRICTED

            # Claim group — prefer LLM output, fall back to inference
            claim_group = result.get("claim_group") or _infer_claim_group(ct_id)

            classification = ClaimClassification(
                ct_id=ct_id,
                claim_type_name=result["claim_type_name"],
                claim_group=claim_group,
                secondary_ct_id=result.get("secondary_ct_id"),
                audience_constraint=audience,
                is_modifier_only=is_modifier,
                is_study_design=is_study_design,
                mapping_pending=mapping_pending,
                confidence=result.get("confidence", 0.9),
            )

            picot = PICOTComponents(
                population=picot_data.get("population"),
                intervention=picot_data.get("intervention"),
                comparator=picot_data.get("comparator"),
                outcome=picot_data.get("outcome"),
                timeframe=picot_data.get("timeframe"),
            )

            logger.info(
                f"Classified claim as {classification.ct_id} "
                f"(group={claim_group}, {classification.claim_type_name}) "
                f"audience={audience.value} modifier={is_modifier} "
                f"study_design={is_study_design} "
                f"confidence={classification.confidence:.2f}"
            )

            if mapping_pending:
                logger.warning(
                    f"CT-ID {ct_id} is a Study Design type (A11) with no reference "
                    f"mapping yet. Retrieval will return empty results for this claim."
                )

            return classification, picot

        except Exception as e:
            logger.error(f"Claim classification failed: {e}")
            # Fallback: generic efficacy claim
            return (
                ClaimClassification(
                    ct_id="CT-201",
                    claim_type_name="Primary-endpoint efficacy (fallback)",
                    claim_group="A2",
                    audience_constraint=AudienceConstraint.UNRESTRICTED,
                    is_modifier_only=False,
                    is_study_design=False,
                    mapping_pending=False,
                    confidence=0.0,
                ),
                PICOTComponents(),
            )

