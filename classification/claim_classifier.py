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


# Mapping from CT-ID to claim_group A-code.
# Uses exact full CT-IDs to avoid prefix ambiguity (e.g. CT-801 vs CT-80x).
_CT_GROUP_MAP: dict = {
    # A1 Indication & Regulatory
    "CT-101": "A1", "CT-102": "A1", "CT-103": "A1", "CT-104": "A1",
    "CT-105": "A1", "CT-106": "A1", "CT-107": "A1", "CT-108": "A1",
    "CT-109": "A1", "CT-110": "A1",
    # A2 Efficacy
    "CT-201": "A2", "CT-202": "A2", "CT-203": "A2", "CT-204": "A2",
    "CT-205": "A2", "CT-206": "A2", "CT-207": "A2", "CT-208": "A2", "CT-209": "A2",
    # A3 Safety & Tolerability
    "CT-301": "A3", "CT-302": "A3", "CT-303": "A3", "CT-304": "A3",
    "CT-305": "A3", "CT-306": "A3", "CT-307": "A3", "CT-308": "A3",
    "CT-309": "A3", "CT-310": "A3", "CT-311": "A3",
    # A4 Comparative
    "CT-401": "A4", "CT-402": "A4", "CT-403": "A4", "CT-404": "A4",
    "CT-405": "A4", "CT-406": "A4", "CT-407": "A4", "CT-408": "A4", "CT-409": "A4",
    # A5 Pharmacology / MoA
    "CT-501": "A5", "CT-502": "A5", "CT-503": "A5", "CT-504": "A5",
    "CT-505": "A5", "CT-506": "A5", "CT-507": "A5",
    # A6 Dosing, Administration & Handling
    "CT-601": "A6", "CT-602": "A6", "CT-603": "A6", "CT-604": "A6",
    "CT-605": "A6", "CT-606": "A6", "CT-607": "A6", "CT-608": "A6",
    # A7 Disease-State / Epidemiology
    "CT-701": "A7", "CT-702": "A7", "CT-703": "A7", "CT-704": "A7",
    "CT-705": "A7", "CT-706": "A7",
    # A8 Patient-Centric
    "CT-801": "A8", "CT-802": "A8", "CT-803": "A8", "CT-804": "A8",
    "CT-805": "A8", "CT-806": "A8", "CT-807": "A8",
    # A9 Economic / HCEI
    "CT-901": "A9", "CT-902": "A9", "CT-903": "A9", "CT-904": "A9",
    "CT-905": "A9", "CT-906": "A9", "CT-907": "A9", "CT-908": "A9", "CT-909": "A9",
    # A10 Off-Label / Scientific-Exchange + Evidence-type modifiers
    "CT-B01": "A10", "CT-B02": "A10", "CT-B03": "A10", "CT-B04": "A10",
    "CT-A01": "A10", "CT-A02": "A10", "CT-A03": "A10", "CT-A04": "A10",
    "CT-A05": "A10", "CT-A06": "A10", "CT-A07": "A10", "CT-A08": "A10",
    # A11 Study Design / Methodology (pending reference mapping)
    "CT-D01": "A11", "CT-D02": "A11", "CT-D03": "A11",
    "CT-D04": "A11", "CT-D05": "A11", "CT-D06": "A11",
}


def _infer_claim_group(ct_id: str) -> Optional[str]:
    """Infer the A-group from a CT-ID string.

    Uses exact full CT-IDs for known types. Falls back to longest-prefix
    match for any unknown future CT-IDs.
    """
    # Exact lookup (fast path, no ambiguity)
    if ct_id in _CT_GROUP_MAP:
        return _CT_GROUP_MAP[ct_id]
    # Longest-prefix match for unknown future IDs
    for prefix in sorted(_CT_GROUP_MAP, key=len, reverse=True):
        if ct_id.startswith(prefix):
            return _CT_GROUP_MAP[prefix]
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
                # Note: gpt-5.x models only support temperature=1 (default).
                # Omit temperature parameter to avoid 400 errors.
                _call_kwargs = dict(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self._system_prompt},
                        {"role": "user", "content": claim_text},
                    ],
                    response_format={"type": "json_object"},
                )
                # Only pass temperature if model supports it (not gpt-5.x)
                if not self.model.startswith("gpt-5"):
                    _call_kwargs["temperature"] = 0.1
                response = self._client.chat.completions.create(**_call_kwargs)
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

