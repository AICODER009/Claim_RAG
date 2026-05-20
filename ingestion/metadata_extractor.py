"""Bibliographic Metadata Extractor — extracts citation info from document headers.

Uses GPT structured output (Pydantic) to extract authors, title, journal,
year, DOI from the first ~400 words of each parsed markdown document.

Required for audit trail (Section 8.1): "Full Citation", "DOI".
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic response schema
# ---------------------------------------------------------------------------

class DocMetadata(BaseModel):
    """Structured bibliographic metadata extracted from document header."""
    title: str = Field(..., description="Full title of the document")
    authors: List[str] = Field(
        default_factory=list,
        description="Authors in order, format: 'Last First' or 'Last AB'"
    )
    journal: Optional[str] = Field(None, description="Journal name (abbreviated)")
    year: Optional[int] = Field(None, description="Publication year")
    doi: Optional[str] = Field(None, description="DOI without URL prefix")
    volume: Optional[str] = Field(None, description="Volume number")
    issue: Optional[str] = Field(None, description="Issue number")
    page_range: Optional[str] = Field(None, description="Page range e.g. '123-145'")
    publisher: Optional[str] = Field(None, description="Publisher or sponsor")
    trial_id: Optional[str] = Field(None, description="Clinical trial ID e.g. 'NCT04280718'")


METADATA_PROMPT = """You are a biomedical librarian. Extract bibliographic metadata from the opening text of this pharmaceutical/clinical document.

RULES:
1. Extract ONLY what is explicitly stated in the text.
2. Do NOT guess or infer missing fields — leave them null.
3. For authors, preserve the order as they appear.
4. For DOI, extract just the DOI string (e.g., "10.1016/S1474-4422(24)00250-1"), not the full URL.
5. For prescribing information or regulatory documents, the "title" is the drug brand name + document type.
"""


# ---------------------------------------------------------------------------
# Extractor class
# ---------------------------------------------------------------------------

class MetadataExtractor:
    """Extract bibliographic metadata using GPT structured output.

    Primary: GPT-5.2. Fallback: Claude on quota errors.
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
        self._openai_quota_hit = False

        self._anthropic_client = None
        self._anthropic_model = anthropic_model
        if anthropic_api_key:
            try:
                import anthropic
                self._anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
            except ImportError:
                pass

    def extract(self, markdown_text: str, filename: str = "", max_words: int = 600) -> Dict[str, Any]:
        """Extract metadata by combining regex (deep scan) + LLM (structured).

        Strategy:
        1. Regex scans the FULL document for DOI, year, trial_id (cheap, reliable)
        2. LLM reads the first ~600 words for title, authors, journal
        3. Merge: regex wins for structured patterns, LLM wins for natural language

        Args:
            markdown_text: Full document markdown (preprocessed).
            filename: Document filename for fallback title.
            max_words: Words from start sent to LLM.

        Returns:
            Dict with structured bibliographic metadata.
        """
        if not markdown_text or not markdown_text.strip():
            return {}

        # Step 1: Regex on FULL text
        regex_meta = self.extract_without_llm(markdown_text, filename=filename)

        # Step 2: LLM on first ~600 words
        first_page = " ".join(markdown_text.split()[:max_words])
        llm_meta = {}

        if not self._openai_quota_hit:
            try:
                response = self._client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": METADATA_PROMPT},
                        {"role": "user", "content": first_page},
                    ],
                    temperature=0.05,
                    response_format=DocMetadata,
                )
                result: DocMetadata = response.choices[0].message.parsed
                self._call_count += 1
                if result:
                    llm_meta = result.model_dump(exclude_none=True)

            except Exception as e:
                if "429" in str(e) or "insufficient_quota" in str(e):
                    logger.warning("OpenAI quota hit — switching to Claude for metadata")
                    self._openai_quota_hit = True
                    llm_meta = self._extract_claude(first_page)
                else:
                    logger.error(f"GPT metadata extraction failed: {e}")
        else:
            llm_meta = self._extract_claude(first_page)

        # Step 3: Merge — regex wins for DOI/year/trial_id, LLM wins for rest
        meta: Dict[str, Any] = {}

        # LLM fields first (title, authors, journal, volume, issue, etc.)
        meta.update(llm_meta)

        # Regex overwrites DOI/year/trial_id (more reliable — scans full doc)
        if regex_meta.get("doi"):
            meta["doi"] = regex_meta["doi"]
        if regex_meta.get("year") and not meta.get("year"):
            meta["year"] = regex_meta["year"]
        if regex_meta.get("trial_id"):
            meta["trial_id"] = regex_meta["trial_id"]

        # Format authors string
        if meta.get("authors"):
            meta["authors_str"] = ", ".join(meta["authors"][:3])
            if len(meta["authors"]) > 3:
                meta["authors_str"] += " et al."

        # Fallback title from filename
        if not meta.get("title") and filename:
            meta["title"] = filename

        logger.info(
            f"Metadata: '{meta.get('title', '?')[:50]}...' "
            f"({meta.get('year', '?')}) doi={meta.get('doi', 'none')}"
        )
        return meta

    def _extract_claude(self, first_page_text: str) -> Dict[str, Any]:
        """Fallback: extract metadata using Claude."""
        if not self._anthropic_client:
            return {}

        try:
            import json as _json

            prompt = (
                METADATA_PROMPT
                + "\n\nReturn ONLY valid JSON with fields: title, authors (array), "
                "journal, year, doi, volume, issue, page_range, publisher, trial_id."
            )

            response = self._anthropic_client.messages.create(
                model=self._anthropic_model,
                max_tokens=1024,
                temperature=0.05,
                messages=[
                    {"role": "user", "content": f"{prompt}\n\n{first_page_text}"},
                ],
            )

            raw_text = response.content[0].text
            json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if not json_match:
                return {}

            result = _json.loads(json_match.group())
            self._call_count += 1

            # Clean nulls
            return {k: v for k, v in result.items() if v is not None}

        except Exception as e:
            logger.error(f"Claude metadata extraction failed: {e}")
            return {}

    def extract_without_llm(self, markdown_text: str, filename: str = "") -> Dict[str, Any]:
        """Regex-only fallback — extract what we can without any LLM.

        Useful for cost reduction: DOI, year, and trial ID are easy to regex.
        Title and authors are harder but we can get a rough approximation.
        """
        meta: Dict[str, Any] = {}

        # DOI — scan deep (footers, headers, after abstract)
        doi_match = re.search(r"(?:doi\.org/|doi:?\s*)(10\.\d{4,9}/[^\s,]+)", markdown_text[:8000], re.IGNORECASE)
        if doi_match:
            meta["doi"] = doi_match.group(1).rstrip(".,;)")
        else:
            doi_bare = re.search(r"(10\.\d{4,9}/[^\s,]+)", markdown_text[:8000])
            if doi_bare:
                meta["doi"] = doi_bare.group(1).rstrip(".,;)")

        # Year (4-digit near start)
        year_match = re.search(r"\b(19[89]\d|20[012]\d)\b", markdown_text[:2000])
        if year_match:
            meta["year"] = int(year_match.group())

        # Trial ID
        trial_match = re.search(r"NCT\d{7,8}", markdown_text[:5000])
        if trial_match:
            meta["trial_id"] = trial_match.group()

        # Title: first H1 heading
        h1_match = re.search(r"^#\s+(.+)$", markdown_text[:2000], re.MULTILINE)
        if h1_match:
            meta["title"] = re.sub(r"[*_`]", "", h1_match.group(1)).strip()

        # Use filename as fallback title
        if not meta.get("title") and filename:
            meta["title"] = filename

        return meta

    @property
    def stats(self) -> dict:
        return {"calls": self._call_count}
