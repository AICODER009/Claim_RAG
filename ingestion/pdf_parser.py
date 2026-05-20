"""LandingAI PDF Parser — layout-aware document extraction.

Uses LandingAI's Agentic Document Extraction (ADE) to parse PDFs into
structured chunks with type classification and visual grounding.

ACTUAL API RESPONSE STRUCTURE (from docs + testing):
- chunks[]: each has {id, markdown, type, grounding: {box: {left,top,right,bottom}, page}}
- markdown: full document concatenated markdown
- grounding: global object mapping chunk/table/cell IDs to detailed grounding
- splits[]: page-level splits with chunk references
- metadata: {filename, page_count, duration_ms, credit_usage, job_id, version}

Chunk types found in pharma PDFs:
- text: paragraphs, headings, body text
- table: HTML <table> elements with cell IDs
- figure: descriptions wrapped in <::description: figure::>
- marginalia: page numbers, headers, footers
- logo: company/journal logos

Table markup: <table id="0-1"><tr><td id="0-2">Cell</td></tr></table>
Figure markup: <::description text: figure::>
Anchor tags: <a id='uuid'></a> at start of each chunk
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ParsedChunk:
    """A single chunk from LandingAI parsing."""
    chunk_id: str         # UUID from LandingAI
    text: str             # Markdown content (anchor tags stripped)
    raw_markdown: str     # Original markdown including anchor tags
    chunk_type: str       # "text", "table", "figure", "marginalia", "logo"
    page: int             # 0-indexed page number
    bbox: Optional[Dict[str, float]] = None  # {left, top, right, bottom} normalized
    confidence: Optional[float] = None       # From global grounding (DPT-2)


@dataclass
class ParseResult:
    """Complete result from parsing a PDF."""
    chunks: List[ParsedChunk]
    markdown: str                      # Full document markdown
    grounding: Dict[str, Any]          # Global grounding object
    splits: List[Dict[str, Any]]       # Page-level splits
    metadata: Dict[str, Any]           # API metadata (page_count, duration_ms, etc.)
    filename: str

    @property
    def total_pages(self) -> int:
        return self.metadata.get("page_count", 0)

    @property
    def doc_metadata(self) -> Dict[str, Any]:
        """Backwards compat — returns the API metadata."""
        return self.metadata


class LandingAIPDFParser:
    """PDF parser using LandingAI ADE API.

    Uses the Parse Jobs API (async) for large documents.
    Caches full API response as JSON to avoid re-parsing.
    """

    # Regex to strip <a id='...'></a> anchor tags from markdown
    _ANCHOR_RE = re.compile(r"<a\s+id=['\"].*?['\"]>\s*</a>")

    def __init__(self, api_key: str, cache_dir: Optional[Path] = None):
        self.api_key = api_key
        self.cache_dir = cache_dir
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)

    async def parse(self, pdf_path: Path) -> ParseResult:
        """Parse a PDF into structured chunks.

        Checks cache first; if not cached, calls LandingAI API.
        """
        # Check cache
        cached = self._load_cache(pdf_path)
        if cached:
            logger.info(f"Loaded cached parse for: {pdf_path.name}")
            return cached

        # Parse via LandingAI API
        logger.info(f"Parsing via LandingAI: {pdf_path.name}")
        raw_response = await self._call_api(pdf_path)

        # Save full JSON cache
        self._save_cache(pdf_path, raw_response)

        # Convert to ParseResult
        return self._convert_response(raw_response, pdf_path.name)

    async def _call_api(self, pdf_path: Path) -> dict:
        """Call the LandingAI Parse Jobs API."""
        import httpx
        import asyncio

        headers = {"Authorization": f"Bearer {self.api_key}"}
        base_url = "https://api.va.landing.ai/v1/ade/parse/jobs"

        async with httpx.AsyncClient(timeout=300.0) as client:
            # Submit job
            with open(pdf_path, "rb") as f:
                files = {"document": (pdf_path.name, f, "application/pdf")}
                response = await client.post(base_url, files=files, headers=headers)

            if response.status_code not in (200, 201, 202):
                logger.error(f"LandingAI error: {response.status_code} - {response.text[:300]}")
                raise RuntimeError(f"LandingAI API error: {response.status_code}")

            job_data = response.json()
            job_id = job_data.get("job_id")
            if not job_id:
                raise RuntimeError(f"No job_id in response: {job_data}")

            logger.info(f"Job {job_id} submitted, polling...")

            # Poll for completion
            while True:
                status_resp = await client.get(f"{base_url}/{job_id}", headers=headers)
                status_data = status_resp.json()
                status = status_data.get("status", "unknown")

                if status == "completed":
                    break
                elif status in ("failed", "error"):
                    raise RuntimeError(f"Job {job_id} failed: {status_data}")

                await asyncio.sleep(5)

        # Extract the result — may be at top level or nested in "data"
        if "chunks" in status_data:
            return status_data
        elif "data" in status_data and "chunks" in status_data["data"]:
            return status_data["data"]
        else:
            return status_data

    def _convert_response(self, data: dict, filename: str) -> ParseResult:
        """Convert raw API JSON to ParseResult with proper typing."""
        raw_chunks = data.get("chunks", [])
        global_grounding = data.get("grounding", {})

        chunks = []
        for chunk in raw_chunks:
            chunk_id = chunk.get("id", "")
            chunk_type = chunk.get("type", "text")
            raw_markdown = chunk.get("markdown", "")

            # Strip anchor tags for clean text
            text = self._ANCHOR_RE.sub("", raw_markdown).strip()

            # Get grounding from chunk-level
            chunk_grounding = chunk.get("grounding", {})
            page = chunk_grounding.get("page", 0)
            bbox = chunk_grounding.get("box")  # {left, top, right, bottom}

            # Get confidence from global grounding if available
            confidence = None
            if chunk_id in global_grounding:
                confidence = global_grounding[chunk_id].get("confidence")

            if text:  # Skip empty chunks
                chunks.append(ParsedChunk(
                    chunk_id=chunk_id,
                    text=text,
                    raw_markdown=raw_markdown,
                    chunk_type=chunk_type,
                    page=page,
                    bbox=bbox,
                    confidence=confidence,
                ))

        return ParseResult(
            chunks=chunks,
            markdown=data.get("markdown", ""),
            grounding=global_grounding,
            splits=data.get("splits", []),
            metadata=data.get("metadata", {}),
            filename=filename,
        )

    def _fallback_pymupdf(self, pdf_path: Path) -> ParseResult:
        """Last-resort fallback using PyMuPDF (no layout awareness)."""
        logger.warning(f"Using PyMuPDF fallback for: {pdf_path.name}")
        try:
            import fitz
            doc = fitz.open(str(pdf_path))
            chunks = []
            for page_num, page in enumerate(doc):
                text = page.get_text()
                if text.strip():
                    chunks.append(ParsedChunk(
                        chunk_id=f"pymupdf-page-{page_num}",
                        text=text.strip(),
                        raw_markdown=text.strip(),
                        chunk_type="text",
                        page=page_num,
                    ))
            total_pages = len(doc)
            doc.close()
            return ParseResult(
                chunks=chunks,
                markdown="\n\n".join(c.text for c in chunks),
                grounding={},
                splits=[],
                metadata={"page_count": total_pages, "parser": "pymupdf_fallback"},
                filename=pdf_path.name,
            )
        except ImportError:
            logger.error("PyMuPDF not available")
            return ParseResult(
                chunks=[], markdown="", grounding={}, splits=[],
                metadata={"page_count": 0}, filename=pdf_path.name,
            )

    # ---------------------------------------------------------------
    # Caching — saves FULL API response
    # ---------------------------------------------------------------

    def _cache_path(self, pdf_path: Path) -> Optional[Path]:
        if not self.cache_dir:
            return None
        return self.cache_dir / f"{pdf_path.stem}.json"

    def _load_cache(self, pdf_path: Path) -> Optional[ParseResult]:
        """Load cached parse result."""
        cache_path = self._cache_path(pdf_path)
        if not cache_path or not cache_path.exists():
            # Check next to PDF as fallback
            alt = pdf_path.with_suffix(".json")
            if alt.exists():
                cache_path = alt
            else:
                return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return self._convert_response(data, pdf_path.name)
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return None

    def _save_cache(self, pdf_path: Path, response: dict) -> None:
        """Save full API response as JSON."""
        cache_path = self._cache_path(pdf_path)
        if not cache_path:
            return
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(response, f, ensure_ascii=False, indent=2)
        logger.info(f"Cached: {cache_path}")
