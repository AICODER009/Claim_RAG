"""Claim-to-Question Rewriter for MedCPT Query Encoder.

MedCPT's Query Encoder was trained on PubMed search queries (question-form),
NOT assertion-form marketing claims. This module transforms:

  "Efgartigimod reduced relapse risk by 61%"
  → "What was the relapse risk reduction with efgartigimod?"

Keeps rewrites short (≤30 words) to match MedCPT's training distribution.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

REWRITE_SYSTEM_PROMPT = """You convert pharmaceutical marketing claims into short PubMed-style search questions.

Rules:
1. Output ONLY the question — no explanation, no quotes, no prefix.
2. Keep it under 30 words.
3. Preserve key medical terms, drug names, and numeric values.
4. Frame as a question seeking the evidence behind the claim.
5. Do NOT add information not present in the original claim.

Examples:
- Claim: "Efgartigimod reduced relapse risk by 61%"
  Question: What is the relapse risk reduction with efgartigimod treatment?

- Claim: "VYVGART Hytrulo is indicated for CIDP in adults"  
  Question: What are the approved indications for VYVGART Hytrulo?

- Claim: "The most common adverse reactions were headache (26%) and nasopharyngitis (12%)"
  Question: What are the most common adverse reactions and their rates for this treatment?

- Claim: "Efgartigimod binds to FcRn, reducing pathogenic IgG levels"
  Question: What is the mechanism of action of efgartigimod involving FcRn binding?
"""


class ClaimRewriter:
    """Transform assertion-form claims into question-form queries."""

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-5.5",
        api_key: str = "",
    ):
        self.provider = provider
        self.model = model

        if provider == "openai":
            from openai import OpenAI
            self._client = OpenAI(api_key=api_key)
        elif provider == "anthropic":
            import anthropic
            self._client = anthropic.Anthropic(api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def rewrite(self, claim_text: str) -> str:
        """Rewrite a claim into a PubMed-style question.

        Args:
            claim_text: The pharmaceutical marketing claim.

        Returns:
            A short question (≤30 words) suitable for MedCPT Query Encoder.
        """
        try:
            if self.provider == "openai":
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": REWRITE_SYSTEM_PROMPT},
                        {"role": "user", "content": claim_text},
                    ],
                    temperature=0,  # deterministic: same claim = same query every run
                    max_completion_tokens=100,
                )
                question = response.choices[0].message.content.strip()

            elif self.provider == "anthropic":
                response = self._client.messages.create(
                    model=self.model,
                    max_tokens=100,
                    system=REWRITE_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": claim_text}],
                    temperature=0,  # deterministic: same claim = same query every run
                )
                question = response.content[0].text.strip()

            # Clean up: remove quotes if LLM wrapped it
            question = question.strip('"\'')

            # Ensure it ends with ?
            if not question.endswith("?"):
                question += "?"

            logger.info(f"Rewrite: '{claim_text[:60]}...' -> '{question}'")
            return question

        except Exception as e:
            logger.error(f"Claim rewrite failed: {e}")
            # Fallback: use claim as-is (MedCPT can still encode it)
            return claim_text
