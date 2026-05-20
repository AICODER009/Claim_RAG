"""Markdown pre-processor for LlamaParser output.

Two cleaning passes before chunking:
1. Strip page furniture (<page_header>, <page_footer> tags)
2. Remove fabricated figure-derived <table> blocks that lack a
   real "Table N" caption within 6 preceding lines.

This module is PARSER-SPECIFIC to LlamaParser output format.
"""

from __future__ import annotations

import re
import logging

logger = logging.getLogger(__name__)


def strip_page_furniture(md: str) -> str:
    """Remove <page_header> and <page_footer> blocks.

    LlamaParser wraps running headers/footers in these tags.
    They contain journal name, page numbers, author surnames —
    noise for embedding but useful if you ever need page provenance.
    """
    before = len(md)
    md = re.sub(
        r"<page_(header|footer)>.*?</page_\1>",
        "",
        md,
        flags=re.DOTALL,
    )
    removed = before - len(md)
    if removed > 0:
        logger.debug(f"Stripped {removed} chars of page furniture")
    return md


def filter_fake_tables(md: str) -> str:
    """Remove <table> blocks NOT preceded by a 'Table N' caption.

    LlamaParser sometimes digitizes scatter-plot figures into HTML
    tables with fabricated "Patient N" labels. The real tables in
    clinical papers always have a "Table 1", "Table 2" etc. caption
    within a few lines above. Figure-derived tables do not.

    This filter was validated on Al-Zuhairy 2021 (3 fake tables
    removed, 4 real tables kept) and confirmed safe on Al-Zuhairy
    2022 and Adrichem 2022 (zero false positives).
    """
    lines = md.split("\n")
    result = []
    i = 0
    tables_kept = 0
    tables_dropped = 0

    while i < len(lines):
        # Detect start of a <table> block
        if "<table" in lines[i].lower():
            # Look back up to 8 non-blank lines for "Table \d+"
            lookback_lines = []
            j = i - 1
            while j >= 0 and len(lookback_lines) < 8:
                if lines[j].strip():
                    lookback_lines.append(lines[j])
                j -= 1

            has_caption = any(
                re.search(r"Table\s+\d+", line, re.IGNORECASE)
                for line in lookback_lines
            )

            if has_caption:
                # Keep the real table
                while i < len(lines):
                    result.append(lines[i])
                    if "</table>" in lines[i].lower():
                        i += 1
                        break
                    i += 1
                tables_kept += 1
            else:
                # Skip the fabricated table
                while i < len(lines) and "</table>" not in lines[i].lower():
                    i += 1
                if i < len(lines):
                    i += 1  # skip the </table> line too
                tables_dropped += 1
        else:
            result.append(lines[i])
            i += 1

    if tables_dropped > 0:
        logger.info(
            f"Tables: kept {tables_kept}, dropped {tables_dropped} "
            f"(no 'Table N' caption)"
        )
    return "\n".join(result)


def strip_image_refs(md: str) -> str:
    """Remove broken image references like ![caption](page_N_image_M.jpg).

    LlamaParser embeds these references but the image files are not
    available in the pipeline. Strip them to avoid embedding noise.
    Keep the alt text if it's descriptive (>20 chars) as it may
    contain useful figure descriptions.
    """
    def _replace_image(match: re.Match) -> str:
        alt_text = match.group(1).strip()
        # Keep descriptive alt text (e.g., figure descriptions)
        if len(alt_text) > 20 and not alt_text.endswith("logo"):
            return f"[Figure: {alt_text}]"
        return ""

    return re.sub(
        r"!\[([^\]]*)\]\([^)]+\.(?:jpg|png|jpeg|gif|svg|webp)[^)]*\)",
        _replace_image,
        md,
        flags=re.IGNORECASE,
    )


def preprocess(md: str, filename: str = "") -> str:
    """Run all pre-processing passes on a LlamaParser markdown file.

    Args:
        md: Raw markdown content from LlamaParser.
        filename: For logging.

    Returns:
        Cleaned markdown ready for chunking.
    """
    logger.info(f"Pre-processing: {filename} ({len(md)} chars)")
    md = strip_page_furniture(md)
    md = filter_fake_tables(md)
    md = strip_image_refs(md)

    # Collapse excessive blank lines (>2 → 2)
    md = re.sub(r"\n{3,}", "\n\n", md)

    logger.info(f"Pre-processing done: {filename} ({len(md)} chars)")
    return md
