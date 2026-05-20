"""Reference Document Typizer — assigns RT-ID during ingestion.

Stage 1 of the pipeline: reads the first pages of a PDF and
classifies it into a Reference Document Type (RT-ID).

ANTI-HALLUCINATION MEASURES:
1. Structured Outputs via client.beta.chat.completions.parse() — 
   the model CANNOT return invalid JSON or wrong field types.
2. Pydantic Enum constraint on `category` — only B1-B9 are valid.
3. Chain-of-thought `reasoning` field — forces the model to explain
   BEFORE committing to a classification, reducing snap-judgment errors.
4. Temperature 0.1 — near-deterministic for classification tasks.
"""

from __future__ import annotations

import json
import logging
from enum import Enum
from pathlib import Path
from typing import Optional, Literal

from pydantic import BaseModel, Field

from ..schemas import ReferenceTypization, ReferenceCategory
from ..prompts.typization_prompt import build_typization_prompt

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Structured Output Schema (Pydantic) for constrained decoding
# ---------------------------------------------------------------------------

class TypizationResponse(BaseModel):
    """Schema enforced at the token-generation level by OpenAI.
    
    The model CANNOT return values outside this schema.
    This prevents:
    - Hallucinated field names
    - Invalid category codes (only B1-B9 allowed)
    - Missing required fields
    """
    reasoning: str = Field(
        ...,
        description="Step-by-step explanation of WHY this classification was chosen. "
                    "Think through: title cues, filename cues, structural cues, "
                    "content cues. This field is generated FIRST to force chain-of-thought."
    )
    rt_id: str = Field(
        ...,
        description="Reference type ID from the taxonomy, e.g. RT-101, RT-301, RT-402"
    )
    category: Literal["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9"] = Field(
        ...,
        description="Top-level category code. MUST be one of B1-B9."
    )
    reference_type_name: str = Field(
        ...,
        description="Human-readable name of the reference type, e.g. 'US Prescribing Information'"
    )
    confidence: float = Field(
        ...,
        ge=0.0, le=1.0,
        description="Classification confidence between 0.0 and 1.0"
    )


class Typizer:
    """Classify reference documents into RT-IDs using an LLM.
    
    Uses OpenAI Structured Outputs (constrained decoding) to prevent
    hallucinated classifications. The model is forced to:
    1. Explain its reasoning FIRST (chain-of-thought)
    2. Return only valid B1-B9 category codes (Literal type)
    3. Return well-formed JSON matching the TypizationResponse schema
    """

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        api_key: str = "",
        taxonomy_path: Optional[Path] = None,
    ):
        self.provider = provider
        self.model = model
        self.api_key = api_key

        # Load the taxonomy text for prompt context
        if taxonomy_path and taxonomy_path.exists():
            self._taxonomy_text = taxonomy_path.read_text(encoding="utf-8")
        else:
            self._taxonomy_text = ""
            logger.warning("No taxonomy file found — typization will have no context")

        self._system_prompt = build_typization_prompt(self._taxonomy_text)

        # Initialize LLM client
        if provider == "openai":
            from openai import OpenAI
            self._client = OpenAI(api_key=api_key)
        elif provider == "anthropic":
            import anthropic
            self._client = anthropic.Anthropic(api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def classify(self, document_text: str, filename: str = "") -> ReferenceTypization:
        """Classify a reference document into an RT-ID.

        Args:
            document_text: Text from the first 2-3 pages of the PDF.
            filename: Original filename (provides additional cues).

        Returns:
            ReferenceTypization with rt_id, category, name, confidence.
        """
        user_message = f"## Document Filename\n{filename}\n\n## Document Text (First Pages)\n{document_text[:8000]}"

        try:
            if self.provider == "openai":
                # Use structured outputs — constrained decoding prevents hallucination
                try:
                    response = self._client.beta.chat.completions.parse(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": self._system_prompt},
                            {"role": "user", "content": user_message},
                        ],
                        temperature=0.1,
                        response_format=TypizationResponse,
                    )
                    parsed = response.choices[0].message.parsed
                    
                    logger.info(
                        f"Typized '{filename}' as {parsed.rt_id} ({parsed.reference_type_name}) "
                        f"[conf={parsed.confidence:.2f}]"
                    )
                    logger.debug(f"Typization reasoning: {parsed.reasoning}")

                    return ReferenceTypization(
                        rt_id=parsed.rt_id,
                        category=ReferenceCategory(parsed.category),
                        reference_type_name=parsed.reference_type_name,
                        confidence=parsed.confidence,
                    )
                except Exception as parse_err:
                    # Fallback to legacy json_object mode if parse() not supported
                    logger.warning(
                        f"Structured output failed ({parse_err}), "
                        f"falling back to json_object mode"
                    )
                    return self._classify_legacy(user_message)

            elif self.provider == "anthropic":
                return self._classify_anthropic(user_message, filename)

        except Exception as e:
            logger.error(f"Typization failed for '{filename}': {e}")
            # Fallback: generic journal article
            return ReferenceTypization(
                rt_id="RT-301",
                category=ReferenceCategory.B3,
                reference_type_name="Peer-reviewed full-text journal article (fallback)",
                confidence=0.0,
            )

    def _classify_legacy(self, user_message: str) -> ReferenceTypization:
        """Legacy classification using json_object mode (no schema enforcement)."""
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        return ReferenceTypization(
            rt_id=result["rt_id"],
            category=ReferenceCategory(result["category"]),
            reference_type_name=result["reference_type_name"],
            confidence=result.get("confidence", 0.9),
        )

    def _classify_anthropic(self, user_message: str, filename: str) -> ReferenceTypization:
        """Anthropic classification (no structured output, uses json parsing)."""
        response = self._client.messages.create(
            model=self.model,
            max_tokens=500,
            system=self._system_prompt,
            messages=[{"role": "user", "content": user_message}],
            temperature=0.1,
        )
        result = json.loads(response.content[0].text)
        logger.info(f"Typized '{filename}' as {result['rt_id']} ({result['reference_type_name']})")

        return ReferenceTypization(
            rt_id=result["rt_id"],
            category=ReferenceCategory(result["category"]),
            reference_type_name=result["reference_type_name"],
            confidence=result.get("confidence", 0.9),
        )
