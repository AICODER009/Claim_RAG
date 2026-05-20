"""Claim Classifier — assigns CT-ID and extracts PICOT.

Stage 2 / Step 1 of the pipeline: a single LLM call that:
  1. Classifies the claim into a CT-ID
  2. Extracts PICOT components for downstream evaluation
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional, Tuple

from ..schemas import ClaimClassification, PICOTComponents
from ..prompts.classification_prompt import build_classification_prompt

logger = logging.getLogger(__name__)


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
            # Try direct parse first
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                # Extract JSON from markdown code block or surrounding text
                import re
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', result_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise ValueError(f"No JSON found in response: {result_text[:200]}")
            picot_data = result.get("picot", {})

            classification = ClaimClassification(
                ct_id=result["ct_id"],
                claim_type_name=result["claim_type_name"],
                secondary_ct_id=result.get("secondary_ct_id"),
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
                f"({classification.claim_type_name}) "
                f"with confidence {classification.confidence:.2f}"
            )

            return classification, picot

        except Exception as e:
            logger.error(f"Claim classification failed: {e}")
            # Fallback: generic efficacy claim
            return (
                ClaimClassification(
                    ct_id="CT-201",
                    claim_type_name="Primary-endpoint efficacy (fallback)",
                    confidence=0.0,
                ),
                PICOTComponents(),
            )
