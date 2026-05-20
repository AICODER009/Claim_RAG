"""Markdown-structure-aware chunker for LlamaParser output.

Replaces the old PySBD-only sentence chunker with a strategy that
uses the document's OWN structure (headings, paragraphs, tables)
as the primary chunking signal.

Design decisions:
- Headings define section boundaries → each chunk knows its section
- Tables split by row-groups → keeps <thead> context with each group
- Markdown pipe-tables detected alongside HTML tables (future-proofing)
- Small paragraphs merge → avoid tiny orphan chunks
- Near-empty chunks (<5 tokens) filtered out
- Large paragraphs split at ~400 tokens → stay under MedCPT's 512 limit
- Section heading prepended to each chunk → retrieval gets context

Token budget:
  MedCPT max_length=512 tokens ≈ 380 words ≈ 2000 chars
  Target chunk: 300-500 tokens (200-400 words, 1000-2500 chars)
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# Approximate tokens: 1 token ≈ 4 chars for English clinical text
CHARS_PER_TOKEN = 4
TARGET_CHUNK_TOKENS = 400
MAX_CHUNK_TOKENS = 500
MIN_CHUNK_TOKENS = 50

TARGET_CHARS = TARGET_CHUNK_TOKENS * CHARS_PER_TOKEN   # ~1600
MAX_CHARS = MAX_CHUNK_TOKENS * CHARS_PER_TOKEN         # ~2000
MIN_CHARS = MIN_CHUNK_TOKENS * CHARS_PER_TOKEN         # ~200


@dataclass
class Chunk:
    """A single chunk ready for embedding."""
    text: str
    section: str = ""           # e.g., "3. Results > 3.1 Characteristics"
    segment_type: str = "text"  # "text", "table", "figure", "reference"
    heading_level: int = 0      # 1 for H1, 2 for H2, etc.
    source_file: str = ""
    chunk_index: int = 0        # position within the document
    char_count: int = 0
    approx_tokens: int = 0


@dataclass
class _Section:
    """Internal: a heading + all content under it until the next heading."""
    heading: str
    level: int          # 1, 2, 3
    blocks: List[_Block] = field(default_factory=list)


@dataclass
class _Block:
    """Internal: a contiguous block of content (paragraph, table, or figure)."""
    text: str
    block_type: str  # "text", "table", "figure", "reference"


class MarkdownChunker:
    """Section-aware chunker for LlamaParser markdown.

    Usage:
        chunker = MarkdownChunker()
        chunks = chunker.chunk(markdown_text, filename="Al-zuhairy 2021")
    """

    def __init__(
        self,
        target_tokens: int = TARGET_CHUNK_TOKENS,
        max_tokens: int = MAX_CHUNK_TOKENS,
        min_tokens: int = MIN_CHUNK_TOKENS,
    ):
        self.target_chars = target_tokens * CHARS_PER_TOKEN
        self.max_chars = max_tokens * CHARS_PER_TOKEN
        self.min_chars = min_tokens * CHARS_PER_TOKEN

    def chunk(self, md: str, filename: str = "") -> List[Chunk]:
        """Chunk a pre-processed markdown document.

        Args:
            md: Pre-processed markdown (after preprocessor.py).
            filename: For metadata.

        Returns:
            List of Chunk objects ready for embedding.
        """
        sections = self._parse_sections(md)
        chunks = self._sections_to_chunks(sections, filename)

        # Filter out near-empty chunks (stray page numbers, OCR artifacts)
        before_filter = len(chunks)
        chunks = [c for c in chunks if c.approx_tokens >= 3 or c.segment_type == "table"]
        # Re-index after filtering
        for i, c in enumerate(chunks):
            c.chunk_index = i

        filtered = before_filter - len(chunks)
        logger.info(
            f"Chunked '{filename}': {len(sections)} sections → "
            f"{len(chunks)} chunks "
            f"(avg {sum(c.approx_tokens for c in chunks) // max(len(chunks), 1)} tokens)"
            f"{f', filtered {filtered} empty' if filtered else ''}"
        )
        return chunks

    # ------------------------------------------------------------------
    # Step 1: Parse markdown into sections
    # ------------------------------------------------------------------

    def _parse_sections(self, md: str) -> List[_Section]:
        """Parse markdown into a list of sections, each starting at a heading."""
        lines = md.split("\n")
        sections: List[_Section] = []
        current_section = _Section(heading="", level=0)

        i = 0
        while i < len(lines):
            line = lines[i]

            # Detect heading
            heading_match = re.match(r"^(#{1,4})\s+(.+)$", line.strip())
            if heading_match:
                # Save previous section if it has content
                if current_section.blocks:
                    sections.append(current_section)

                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()
                # Clean markdown formatting from headings
                heading_text = re.sub(r"[*_`]", "", heading_text).strip()
                current_section = _Section(heading=heading_text, level=level)
                i += 1
                continue

            # Detect <table> block (HTML)
            if "<table" in line.lower():
                table_lines = [line]
                i += 1
                while i < len(lines) and "</table>" not in lines[i].lower():
                    table_lines.append(lines[i])
                    i += 1
                if i < len(lines):
                    table_lines.append(lines[i])  # include </table>
                    i += 1
                current_section.blocks.append(
                    _Block(text="\n".join(table_lines), block_type="table")
                )
                continue

            # Detect markdown pipe table (future-proofing)
            # Pipe tables look like: | Col1 | Col2 | with a separator line |---|---|
            if re.match(r"^\s*\|.+\|\s*$", line) and i + 1 < len(lines) and re.match(r"^\s*\|[-:| ]+\|\s*$", lines[i + 1]):
                pipe_lines = [line]
                i += 1
                while i < len(lines) and re.match(r"^\s*\|.+\|\s*$", lines[i]):
                    pipe_lines.append(lines[i])
                    i += 1
                current_section.blocks.append(
                    _Block(text="\n".join(pipe_lines), block_type="table")
                )
                continue

            # Detect figure/image reference blocks
            if line.strip().startswith("[Figure:") or re.match(
                r"^Figure\s+\d+", line.strip()
            ):
                fig_lines = [line]
                i += 1
                # Collect caption lines (usually 1-3 lines after)
                while i < len(lines) and lines[i].strip() and not lines[i].startswith("#"):
                    fig_lines.append(lines[i])
                    i += 1
                current_section.blocks.append(
                    _Block(text="\n".join(fig_lines), block_type="figure")
                )
                continue

            # Regular text: collect paragraph (delimited by blank lines)
            if line.strip():
                para_lines = [line]
                i += 1
                while i < len(lines) and lines[i].strip() and not lines[i].startswith("#"):
                    # Stop at table or figure start
                    if "<table" in lines[i].lower() or lines[i].strip().startswith("[Figure:"):
                        break
                    para_lines.append(lines[i])
                    i += 1

                para_text = " ".join(l.strip() for l in para_lines)
                # Detect reference entries
                if self._is_reference_entry(para_text, current_section.heading):
                    # Split merged reference blocks into individual entries
                    # Some docs have all refs in one giant paragraph: "1. Author... 2. Author..."
                    ref_entries = self._split_reference_block(para_text)
                    for entry in ref_entries:
                        current_section.blocks.append(
                            _Block(text=entry.strip(), block_type="reference")
                        )
                else:
                    current_section.blocks.append(
                        _Block(text=para_text, block_type="text")
                    )
                continue

            # Blank line — skip
            i += 1

        # Don't forget the last section
        if current_section.blocks:
            sections.append(current_section)

        return sections

    # ------------------------------------------------------------------
    # Step 2: Convert sections into chunks
    # ------------------------------------------------------------------

    def _sections_to_chunks(
        self, sections: List[_Section], filename: str
    ) -> List[Chunk]:
        """Convert parsed sections into properly sized chunks."""
        chunks: List[Chunk] = []
        chunk_index = 0

        # Build section breadcrumb path
        heading_stack: List[str] = []

        for section in sections:
            # Update heading stack for breadcrumb
            while heading_stack and len(heading_stack) >= section.level:
                heading_stack.pop()
            if section.heading:
                heading_stack.append(section.heading)
            section_path = " > ".join(heading_stack)

            # Group blocks by type
            text_buffer: List[str] = []
            text_buffer_chars = 0

            for block in section.blocks:
                if block.block_type == "table":
                    # Flush text buffer first
                    if text_buffer:
                        chunks.extend(
                            self._emit_text_chunks(
                                text_buffer, section_path, filename, chunk_index
                            )
                        )
                        chunk_index += len(chunks) - chunk_index
                        text_buffer = []
                        text_buffer_chars = 0

                    # Split oversized tables by row-groups
                    table_chunks = self._split_table_if_needed(
                        block.text, section_path, filename, chunk_index
                    )
                    chunks.extend(table_chunks)
                    chunk_index += len(table_chunks)

                elif block.block_type == "figure":
                    # Flush text buffer
                    if text_buffer:
                        chunks.extend(
                            self._emit_text_chunks(
                                text_buffer, section_path, filename, chunk_index
                            )
                        )
                        chunk_index += len(chunks) - chunk_index
                        text_buffer = []
                        text_buffer_chars = 0

                    chunks.append(
                        self._make_chunk(
                            text=block.text,
                            section=section_path,
                            segment_type="figure",
                            filename=filename,
                            index=chunk_index,
                        )
                    )
                    chunk_index += 1

                elif block.block_type == "reference":
                    # Flush text buffer
                    if text_buffer:
                        chunks.extend(
                            self._emit_text_chunks(
                                text_buffer, section_path, filename, chunk_index
                            )
                        )
                        chunk_index += len(chunks) - chunk_index
                        text_buffer = []
                        text_buffer_chars = 0

                    # Each reference entry is its own chunk
                    chunks.append(
                        self._make_chunk(
                            text=block.text,
                            section=section_path,
                            segment_type="reference",
                            filename=filename,
                            index=chunk_index,
                        )
                    )
                    chunk_index += 1

                else:
                    # Text: accumulate into buffer, merge small paragraphs
                    block_chars = len(block.text)

                    # If adding this would exceed target, flush first
                    if (
                        text_buffer
                        and text_buffer_chars + block_chars > self.target_chars
                    ):
                        chunks.extend(
                            self._emit_text_chunks(
                                text_buffer, section_path, filename, chunk_index
                            )
                        )
                        chunk_index += len(chunks) - chunk_index
                        text_buffer = []
                        text_buffer_chars = 0

                    text_buffer.append(block.text)
                    text_buffer_chars += block_chars

            # Flush remaining text buffer at end of section
            if text_buffer:
                chunks.extend(
                    self._emit_text_chunks(
                        text_buffer, section_path, filename, chunk_index
                    )
                )
                chunk_index += len(chunks) - chunk_index

        # Re-index
        for i, chunk in enumerate(chunks):
            chunk.chunk_index = i

        return chunks

    # ------------------------------------------------------------------
    # Table splitting
    # ------------------------------------------------------------------

    def _split_table_if_needed(
        self,
        table_html: str,
        section: str,
        filename: str,
        start_index: int,
    ) -> List[Chunk]:
        """Split an oversized HTML table into row-group chunks.

        Small tables (≤max_tokens) stay atomic.
        Large tables get split by <tr> rows, with the <thead> repeated
        at the top of each chunk so each group has column context.

        Also handles markdown pipe tables by splitting at row boundaries.
        """
        table_tokens = len(table_html) // CHARS_PER_TOKEN
        if table_tokens <= MAX_CHUNK_TOKENS:
            # Small enough — keep as one chunk
            return [
                self._make_chunk(
                    text=table_html,
                    section=section,
                    segment_type="table",
                    filename=filename,
                    index=start_index,
                )
            ]

        # Check if it's a pipe table
        if not table_html.strip().startswith("<"):
            return self._split_pipe_table(table_html, section, filename, start_index)

        # Extract <thead> (or first <tr> in <thead>) as context header
        thead_match = re.search(
            r"(<table[^>]*>.*?<thead>.*?</thead>)",
            table_html,
            re.DOTALL | re.IGNORECASE,
        )
        if thead_match:
            header_html = thead_match.group(1)
        else:
            # No <thead> — use the first <tr> as header
            first_tr = re.search(r"(<table[^>]*>.*?<tr>.*?</tr>)", table_html, re.DOTALL | re.IGNORECASE)
            header_html = first_tr.group(1) if first_tr else "<table>"

        # Extract <caption> if present
        caption_match = re.search(r"<caption>(.*?)</caption>", table_html, re.DOTALL | re.IGNORECASE)
        caption = caption_match.group(0) if caption_match else ""

        # Extract body rows: all <tr> in <tbody> (or after <thead>)
        tbody_match = re.search(r"<tbody>(.*?)</tbody>", table_html, re.DOTALL | re.IGNORECASE)
        if tbody_match:
            body_html = tbody_match.group(1)
        else:
            # No explicit <tbody> — get all rows after the header
            after_header = table_html[len(header_html):] if thead_match else table_html
            body_html = after_header

        body_rows = re.findall(r"<tr>.*?</tr>", body_html, re.DOTALL | re.IGNORECASE)

        if not body_rows:
            # Can't split — return as-is
            return [
                self._make_chunk(
                    text=table_html,
                    section=section,
                    segment_type="table",
                    filename=filename,
                    index=start_index,
                )
            ]

        # Group rows until each group ≈ target_chars
        header_size = len(header_html)
        chunks = []
        idx = start_index
        current_rows = []
        current_size = header_size + len(caption)

        for row in body_rows:
            row_size = len(row)
            if current_rows and current_size + row_size > self.target_chars:
                # Emit this group
                group_html = (
                    header_html
                    + (f"\n  {caption}" if caption else "")
                    + "\n  <tbody>\n"
                    + "\n".join(current_rows)
                    + "\n  </tbody>\n</table>"
                )
                chunks.append(
                    self._make_chunk(
                        text=group_html,
                        section=section,
                        segment_type="table",
                        filename=filename,
                        index=idx,
                    )
                )
                idx += 1
                current_rows = []
                current_size = header_size + len(caption)

            current_rows.append(row)
            current_size += row_size

        # Emit remaining rows
        if current_rows:
            group_html = (
                header_html
                + (f"\n  {caption}" if caption else "")
                + "\n  <tbody>\n"
                + "\n".join(current_rows)
                + "\n  </tbody>\n</table>"
            )
            chunks.append(
                self._make_chunk(
                    text=group_html,
                    section=section,
                    segment_type="table",
                    filename=filename,
                    index=idx,
                )
            )

        logger.debug(
            f"Split table ({table_tokens} tokens) into {len(chunks)} chunks "
            f"({len(body_rows)} rows)"
        )
        return chunks

    def _split_pipe_table(
        self,
        table_text: str,
        section: str,
        filename: str,
        start_index: int,
    ) -> List[Chunk]:
        """Split an oversized markdown pipe table by row groups."""
        lines = table_text.strip().split("\n")
        if len(lines) < 3:
            return [self._make_chunk(table_text, section, "table", filename, start_index)]

        # First two lines are header + separator
        header = lines[0] + "\n" + lines[1]
        body_rows = lines[2:]

        chunks = []
        idx = start_index
        current_rows = []
        current_size = len(header)

        for row in body_rows:
            if current_rows and current_size + len(row) > self.target_chars:
                chunks.append(
                    self._make_chunk(
                        text=header + "\n" + "\n".join(current_rows),
                        section=section,
                        segment_type="table",
                        filename=filename,
                        index=idx,
                    )
                )
                idx += 1
                current_rows = []
                current_size = len(header)

            current_rows.append(row)
            current_size += len(row)

        if current_rows:
            chunks.append(
                self._make_chunk(
                    text=header + "\n" + "\n".join(current_rows),
                    section=section,
                    segment_type="table",
                    filename=filename,
                    index=idx,
                )
            )

        return chunks

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _emit_text_chunks(
        self,
        paragraphs: List[str],
        section: str,
        filename: str,
        start_index: int,
    ) -> List[Chunk]:
        """Merge paragraphs into chunks targeting ~400 tokens.

        If a merged block exceeds max_chars, split at sentence boundary.
        """
        merged = "\n\n".join(paragraphs)

        if len(merged) <= self.max_chars:
            # Fits in one chunk
            if len(merged) < self.min_chars:
                # Too small — will be returned as-is (context still helps)
                pass
            return [
                self._make_chunk(
                    text=merged,
                    section=section,
                    segment_type="text",
                    filename=filename,
                    index=start_index,
                )
            ]

        # Too large — split at sentence boundaries
        return self._split_oversized(merged, section, filename, start_index)

    def _split_oversized(
        self,
        text: str,
        section: str,
        filename: str,
        start_index: int,
    ) -> List[Chunk]:
        """Split oversized text at sentence boundaries.

        Uses a simple regex that respects common medical abbreviations.
        """
        # Split on period/question/exclamation followed by space and uppercase
        raw_splits = re.split(r"(?<=[.?!])\s+(?=[A-Z])", text)

        # Rejoin splits where the preceding "sentence" ends with a known abbreviation
        _ABBREVS = {"Dr", "Mr", "Mrs", "Ms", "Fig", "Figs", "vs", "al", "et",
                    "eg", "ie", "cf", "approx", "incl", "excl", "no", "vol",
                    "Suppl", "Ref", "Prof", "Jr", "Sr", "St", "dept"}
        sentences: List[str] = []
        for part in raw_splits:
            if sentences:
                # Check if previous part ends with an abbreviation
                prev_word = sentences[-1].rstrip(".!? ").rsplit(None, 1)[-1] if sentences[-1].strip() else ""
                if prev_word in _ABBREVS:
                    sentences[-1] = sentences[-1] + " " + part
                    continue
            sentences.append(part)
        if len(sentences) <= 1:
            # Can't split further — return as one chunk
            return [
                self._make_chunk(
                    text=text,
                    section=section,
                    segment_type="text",
                    filename=filename,
                    index=start_index,
                )
            ]

        # Greedily merge sentences until target, with overlap
        # Overlap: last sentence of previous chunk is prepended to next chunk
        # This prevents claim-level context loss at boundaries
        chunks = []
        current = []
        current_len = 0
        idx = start_index
        overlap_sent = None  # last sentence of previous chunk

        for sent in sentences:
            sent_len = len(sent)
            if current and current_len + sent_len > self.target_chars:
                chunk_text = " ".join(current)
                overlap_sent = current[-1] if current else None
                chunks.append(
                    self._make_chunk(
                        text=chunk_text,
                        section=section,
                        segment_type="text",
                        filename=filename,
                        index=idx,
                    )
                )
                idx += 1
                # Start next chunk with overlap sentence
                if overlap_sent:
                    current = [overlap_sent]
                    current_len = len(overlap_sent)
                else:
                    current = []
                    current_len = 0

            current.append(sent)
            current_len += sent_len

        if current:
            chunks.append(
                self._make_chunk(
                    text=" ".join(current),
                    section=section,
                    segment_type="text",
                    filename=filename,
                    index=idx,
                )
            )

        return chunks

    def _make_chunk(
        self,
        text: str,
        section: str,
        segment_type: str,
        filename: str,
        index: int,
    ) -> Chunk:
        """Create a Chunk with section heading prepended.

        Section prefix is capped at ~80 chars to avoid wasting MedCPT's
        512-token budget on long breadcrumbs. When truncating, we keep
        the DEEPEST heading (rightmost in breadcrumb) since it's the most
        specific context signal.
        """
        # Prepend section context for retrieval
        if section and segment_type == "text":
            # Cap prefix to avoid wasting embedding tokens
            display_section = section
            if len(section) > 80:
                # Keep the rightmost (deepest) headings
                parts = section.split(" > ")
                display_section = parts[-1]
                for p in reversed(parts[:-1]):
                    candidate = p + " > " + display_section
                    if len(candidate) > 80:
                        break
                    display_section = candidate
                # Final truncation if a single heading is still too long
                if len(display_section) > 80:
                    display_section = display_section[:77] + "..."
            full_text = f"[{display_section}]\n{text}"
        else:
            full_text = text

        char_count = len(full_text)
        return Chunk(
            text=full_text,
            section=section,  # Full breadcrumb in metadata (not embedded)
            segment_type=segment_type,
            heading_level=0,
            source_file=filename,
            chunk_index=index,
            char_count=char_count,
            approx_tokens=char_count // CHARS_PER_TOKEN,
        )

    @staticmethod
    def _is_reference_entry(text: str, section_heading: str) -> bool:
        """Check if a text block looks like a bibliography reference entry."""
        heading_lower = section_heading.lower()
        if "reference" not in heading_lower and "bibliography" not in heading_lower:
            return False
        # Numbered reference: starts with digit or has DOI/URL
        if re.match(r"^\d+\.\s", text) or "doi" in text.lower() or "https://" in text:
            return True
        # Author-year style: "Smith AB, Jones CD. Title. Journal. 2021"
        if re.match(r"^[A-Z][a-z]+\s+[A-Z]{1,3}", text) and re.search(r"\b\d{4}\b", text):
            return True
        return False

    @staticmethod
    def _split_reference_block(text: str) -> List[str]:
        """Split a merged reference block into individual entries.

        Handles numbered references like:
          "1. Author A... 2. Author B... 3. Author C..."
        Some docs have ALL references concatenated without blank lines.
        """
        # Try splitting on numbered pattern: "N. " where N is 1-999
        # Use lookahead to keep the number with its reference
        entries = re.split(r"(?=\b\d{1,3}\.\s+[A-Z])", text)
        entries = [e.strip() for e in entries if e.strip()]

        if len(entries) > 1:
            return entries

        # If numbered split didn't work, try splitting on author-year patterns
        # "Author AB, Author CD. Title. Journal. Year;"
        entries = re.split(r"(?<=\d{4}[.;])\s+(?=[A-Z][a-z]+\s+[A-Z])", text)
        entries = [e.strip() for e in entries if e.strip()]

        if len(entries) > 1:
            return entries

        # Can't split — return as one block
        return [text]

# ---------------------------------------------------------------------------
# Backwards compatibility: keep the old interface for existing code
# ---------------------------------------------------------------------------

class SentenceChunker:
    """Legacy PySBD chunker — kept for backward compatibility only.

    For new code, use MarkdownChunker instead.
    """

    def __init__(self, language: str = "en"):
        try:
            import pysbd
            self._segmenter = pysbd.Segmenter(language=language, clean=False)
        except ImportError:
            logger.warning("PySBD not installed — using regex fallback")
            self._segmenter = None

    def split(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []
        if self._segmenter:
            sentences = self._segmenter.segment(text)
        else:
            sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) >= 5]


class BlockChunker:
    """Keep text as a single block (no sentence splitting)."""

    def split(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []
        return [text.strip()]


def get_chunker(level: str = "markdown") -> MarkdownChunker | SentenceChunker | BlockChunker:
    """Factory function to get the right chunker.

    Args:
        level: "markdown" (recommended), "sentence" (legacy PySBD), "block".
    """
    if level == "block":
        return BlockChunker()
    if level == "sentence":
        return SentenceChunker()
    return MarkdownChunker()
