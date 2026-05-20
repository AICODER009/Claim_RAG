"""Table Linearizer — converts HTML tables into natural language statements.

Uses GPT structured output (Pydantic) to ensure consistent, hallucination-resistant
conversion of table data into embeddable text.

WHY THIS IS CRITICAL:
  Raw HTML:  <td>Headache</td><td>29%</td><td>22%</td>
  → MedCPT embedding of HTML tags = GARBAGE

  Linearized: "Headache occurred in 29% of efgartigimod patients vs 22% placebo."
  → MedCPT embedding = HIGH QUALITY match for claim queries
"""

from __future__ import annotations

import json
import logging
import re
from typing import List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic response schema — forces structured output, prevents free-form
# ---------------------------------------------------------------------------

class LinearizedRow(BaseModel):
    """One natural-language statement derived from a single table row."""
    statement: str = Field(
        ...,
        description="Declarative sentence stating the data from one row. "
        "Must preserve all numbers, units, and statistical values exactly."
    )
    source_row_index: int = Field(
        ...,
        description="0-based index of the source row in the table body."
    )


class LinearizedTable(BaseModel):
    """Structured output from table linearization."""
    table_label: Optional[str] = Field(
        None,
        description="Table label if present (e.g., 'Table 2', 'Table S1')."
    )
    rows: List[LinearizedRow] = Field(
        ...,
        description="List of linearized statements, one per data row."
    )


# ---------------------------------------------------------------------------
# System prompt with anti-hallucination rules
# ---------------------------------------------------------------------------

TABLE_LINEARIZATION_PROMPT = """You are a clinical data transcriber. Convert each row of the HTML table below into ONE natural-language declarative sentence.

MANDATORY RULES:
1. Every number in the table cell MUST appear in your output EXACTLY as written. Do NOT round, convert units, or paraphrase numbers.
2. Include column headers as context in each statement (e.g., "In the efgartigimod group, headache occurred in 29% of patients").
3. Preserve all statistical values exactly: p-values, confidence intervals, hazard ratios, odds ratios.
4. Preserve all units: %, mg, mg/kg, mL, IU, etc.
5. Do NOT add interpretation, causation, or conclusions. Only state what the table cell contains.
6. Do NOT infer data that is not in the table. If a cell is empty or marked "—" or "N/A", say so explicitly.
7. One statement per body row. Do NOT merge or skip rows.
8. Use the EXACT drug/treatment names from the table, do not substitute generic names.

EXAMPLES:
- Input row: <td>Headache</td><td>29 (15.4%)</td><td>22 (11.8%)</td>
  Column headers: Adverse Event | Efgartigimod (N=188) | Placebo (N=187)
  Output: "Headache was reported in 29 (15.4%) of 188 efgartigimod-treated patients compared with 22 (11.8%) of 187 placebo patients."

- Input row: <td>HR (95% CI)</td><td>0.39 (0.19–0.77)</td><td>p=0.006</td>
  Output: "The hazard ratio was 0.39 (95% CI 0.19–0.77; p=0.006)."
"""


# ---------------------------------------------------------------------------
# Linearizer class
# ---------------------------------------------------------------------------

class TableLinearizer:
    """Convert HTML table chunks into natural language.

    Primary: GPT-5.2 with Pydantic structured output.
    Fallback: Claude (Anthropic) when OpenAI quota is hit (429).
    Last resort: regex HTML strip.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5.2",
        anthropic_api_key: str | None = None,
        anthropic_model: str = "claude-sonnet-4-20250514",
    ):
        from openai import OpenAI
        self._client = OpenAI(api_key=api_key)
        self.model = model
        self._call_count = 0
        self._total_tokens = 0
        self._openai_quota_hit = False

        # Claude fallback
        self._anthropic_client = None
        self._anthropic_model = anthropic_model
        if anthropic_api_key:
            try:
                import anthropic
                self._anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
                logger.info("Claude fallback initialized")
            except ImportError:
                logger.warning("anthropic package not installed — no Claude fallback")

    def linearize(self, table_html: str) -> str:
        """Convert one HTML table into a natural-language paragraph.

        Tries GPT-5.2 first. On quota error, switches to Claude.
        """
        if not table_html or not table_html.strip():
            return ""
        if len(table_html) < 50:
            return self._fallback_strip(table_html)

        # If OpenAI quota already hit, go straight to Claude
        if self._openai_quota_hit:
            return self._linearize_claude(table_html)

        # Try OpenAI first
        try:
            response = self._client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": TABLE_LINEARIZATION_PROMPT},
                    {"role": "user", "content": table_html},
                ],
                temperature=0.05,
                response_format=LinearizedTable,
            )

            result: LinearizedTable = response.choices[0].message.parsed
            self._call_count += 1
            if response.usage:
                self._total_tokens += response.usage.total_tokens

            if not result or not result.rows:
                logger.warning("Linearization returned empty, using fallback")
                return self._fallback_strip(table_html)

            statements = [row.statement for row in result.rows if row.statement.strip()]
            text = " ".join(statements)
            if result.table_label:
                text = f"[{result.table_label}] {text}"
            return text

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "insufficient_quota" in error_str:
                logger.warning("OpenAI quota hit — switching to Claude fallback")
                self._openai_quota_hit = True
                return self._linearize_claude(table_html)
            logger.error(f"Table linearization failed: {e}")
            return self._fallback_strip(table_html)

    def _linearize_claude(self, table_html: str) -> str:
        """Fallback: linearize using Claude with JSON output."""
        if not self._anthropic_client:
            logger.warning("No Claude client — using regex strip fallback")
            return self._fallback_strip(table_html)

        try:
            prompt = (
                TABLE_LINEARIZATION_PROMPT
                + "\n\nReturn a JSON object: {\"table_label\": \"Table X\" or null, "
                "\"rows\": [{\"statement\": \"...\", \"source_row_index\": 0}, ...]}"
            )

            response = self._anthropic_client.messages.create(
                model=self._anthropic_model,
                max_tokens=4096,
                temperature=0.05,
                messages=[
                    {"role": "user", "content": f"{prompt}\n\n{table_html}"},
                ],
            )

            import json as _json
            raw_text = response.content[0].text

            # Extract JSON from response (Claude may wrap in markdown)
            json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if not json_match:
                return self._fallback_strip(table_html)

            result = _json.loads(json_match.group())
            self._call_count += 1

            rows = result.get("rows", [])
            if not rows:
                return self._fallback_strip(table_html)

            statements = [r["statement"] for r in rows if r.get("statement", "").strip()]
            text = " ".join(statements)

            label = result.get("table_label")
            if label:
                text = f"[{label}] {text}"

            return text

        except Exception as e:
            logger.error(f"Claude linearization failed: {e}")
            return self._fallback_strip(table_html)

    def linearize_batch(self, table_htmls: List[str]) -> List[str]:
        """Linearize multiple tables. No batching — GPT API is per-call."""
        results = []
        for i, html in enumerate(table_htmls):
            result = self.linearize(html)
            results.append(result)
            if (i + 1) % 20 == 0:
                logger.info(f"  Linearized {i+1}/{len(table_htmls)} tables...")
        return results

    @property
    def stats(self) -> dict:
        return {
            "calls": self._call_count,
            "total_tokens": self._total_tokens,
        }

    @staticmethod
    def _fallback_strip(html: str) -> str:
        """Minimal fallback: strip HTML tags and collapse whitespace."""
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
        return text
