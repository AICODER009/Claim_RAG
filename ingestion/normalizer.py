"""Text normalization for the MLR-compliant pipeline.

NEW approach vs OLD:
- KEPT: Unicode NFKC, whitespace collapsing
- DROPPED: Token Jaccard overlap, fuzzy string matching (replaced by MedCPT)
- UPGRADED: Numeric tokens now stored WITH context (not bare numbers)

WHY CONTEXT MATTERS:
  Old pipeline: ["32.6", "24"] — ambiguous, "32.6" could be % or mg
  New pipeline: ["32.6% abstinence rate", "24 weeks"] — unambiguous
  
  This is critical for Section 4.1 (Exact Figure Traceability):
  the LLM Judge needs to verify that "32.6%" in the claim means
  "32.6% continuous abstinence" and not "32.6% adverse events".
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import List, Optional


# ---------------------------------------------------------------------------
# Unicode & whitespace normalization
# ---------------------------------------------------------------------------

def normalize_unicode(text: str) -> str:
    """Apply NFKC normalization and collapse whitespace.

    This is applied before embedding to ensure consistent input.
    Handles common PDF extraction artifacts like ligatures and
    non-breaking spaces.
    """
    if not text:
        return ""
    # NFKC: decomposes then composes by compatibility
    # Handles: fi→fi, fl→fl, ½→1/2, etc.
    normalized = unicodedata.normalize("NFKC", text)
    # Replace various dash types with standard hyphen
    normalized = normalized.replace("—", "-").replace("–", "-")
    # Replace non-breaking spaces and other whitespace with regular space
    normalized = re.sub(r"[\xa0\u2000-\u200b\u202f\u205f\u3000]", " ", normalized)
    # Replace middle dots (common in European numbers: "32·6%")
    normalized = normalized.replace("·", ".")
    # Collapse multiple spaces
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


# ---------------------------------------------------------------------------
# Contextualized Numeric Token Extraction
# ---------------------------------------------------------------------------

@dataclass
class NumericToken:
    """A number extracted WITH its surrounding context.
    
    Stores both the raw number and a context window around it
    so the LLM Judge can verify WHAT the number refers to.
    """
    raw_value: str          # "32.6%"
    normalized_value: str   # "32.6%"
    context: str            # "achieved 32.6% continuous abstinence rate at"
    start_pos: int          # Character position in original text
    end_pos: int


# Pattern that matches numeric expressions in clinical text
NUMERIC_PATTERN = re.compile(
    r"""
    (?:p\s*[<>=≤≥]\s*0?\.\d+)          |  # p-values: p<0.001, p = 0.05, p<.001
    (?:\d+\.?\d*\s*%)                   |  # percentages: 32.6%, 80 %
    (?:OR\s*[=:]\s*\d+\.?\d*)           |  # odds ratios: OR=5.3
    (?:HR\s*[=:]\s*\d+\.?\d*)           |  # hazard ratios: HR=0.72
    (?:RR\s*[=:]\s*\d+\.?\d*)           |  # risk ratios: RR=1.5
    (?:CI\s*[,:]\s*\d+\.?\d*\s*[-–]\s*\d+\.?\d*)  |  # CI: 1.2-3.4
    (?:n\s*=\s*\d+)                     |  # sample sizes: n=450
    (?:\d+\.?\d*\s*(?:mg|g|kg|mL|L|mcg|µg|IU|U)\b)  |  # doses: 10mg, 1.5mg
    (?:\d+\.?\d*-fold\b)                |  # fold changes: 4-fold
    (?:\d+\.?\d*\s*x\b)                 |  # ratios: 4x
    (?:\d+\.?\d*)                           # plain numbers: 32.6, 450
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Context window: how many characters around the number to capture
CONTEXT_WINDOW = 40

# Clinical context keywords — numbers near these are DATA, not citations
_CLINICAL_CONTEXT = {
    "%", "mg", "kg", "ml", "g/dl", "mmol", "mcg", "iu",
    "dose", "score", "rate", "mean", "median", "range",
    "ci", "hr", "or", "rr", "p=", "p<", "p>", "n=",
    "fold", "week", "month", "day", "year", "patient",
    "difference", "improvement", "reduction", "increase",
    "baseline", "endpoint", "efficacy", "response",
}


def _is_citation_marker(text: str, raw_value: str, start: int, end: int) -> bool:
    """Detect if a number is a citation/reference marker, not clinical data.

    LlamaParser preserves superscript reference markers in various formats:
      - "treatment.10,11"    (period-glued, no space)
      - "condition.A1,A2"    (letter-number codes)
      - "weakness.3,4,5"     (comma-separated bare refs)
      - "results¹²"          (Unicode superscripts → "12" after NFKC)

    Returns True if the number is likely a citation, False if it's data.
    """
    # Only filter bare integers (not percentages, p-values, doses, CIs)
    if not re.match(r"^\d{1,4}$", raw_value):
        return False

    num = int(raw_value)

    # Heuristic 1: Number immediately after a period with no space
    # e.g., "treatment.10" — this is a citation ref, not "10" as data
    if start >= 1 and text[start - 1] == ".":
        # But "0.47" is a decimal — check if digit before the period
        if start >= 2 and text[start - 2].isdigit():
            return False  # decimal number like 0.47
        return True  # citation like "treatment.10"

    # Heuristic 1b: Number preceded by comma in a citation sequence
    # e.g., ".10,11" — the "11" is preceded by comma, not period
    # Also catches ").12,13" where "13" follows a ref sequence
    if start >= 1 and text[start - 1] == ",":
        # Look backwards past the comma for another number that's a citation
        before_comma = text[max(0, start - 6):start - 1].rstrip()
        if before_comma and before_comma[-1].isdigit():
            # Find where that previous number started
            prev_num_end = len(before_comma)
            prev_num_start = prev_num_end
            while prev_num_start > 0 and before_comma[prev_num_start - 1].isdigit():
                prev_num_start -= 1
            # Check if the char before the previous number is a period or comma
            if prev_num_start > 0 and before_comma[prev_num_start - 1] in ".,":
                return True  # continuation of citation sequence

    # Heuristic 2: Preceded by a letter in a letter-number code (A1, A2, etc.)
    if start >= 1 and text[start - 1].isalpha():
        return True  # e.g., "A1", "B2" in ".A1,A2"

    # Heuristic 3: Bare small number (1-999) without clinical context nearby
    if num < 1000 and not any(
        unit in raw_value.lower() for unit in ["mg", "kg", "ml", "%", "fold"]
    ):
        before = text[max(0, start - 25):start].lower()
        after = text[end:min(len(text), end + 25)].lower()
        nearby = before + " " + after

        # If no clinical context words nearby, likely a citation
        has_clinical_context = any(kw in nearby for kw in _CLINICAL_CONTEXT)
        if not has_clinical_context:
            # Additional check: is this in a comma-separated list of small numbers?
            # e.g., ".3,4,5" or ",10,11"
            surrounding = text[max(0, start - 3):min(len(text), end + 3)]
            if re.search(r"[.,]\d{1,3}[.,]", surrounding):
                return True  # comma-separated ref list

    # Heuristic 4: Author affiliation superscripts
    # e.g., "Hughes, MD, FMedSci,1 Bensa, BSc,1" — number after degree abbreviation + comma
    if num < 100 and start >= 1 and text[start - 1] == ",":
        before_chunk = text[max(0, start - 20):start - 1].strip()
        # Check if preceded by degree/title abbreviation patterns
        if re.search(r"(?:MD|PhD|BSc|MSc|FMedSci|CSc|FRCP|FAAN|DO|RN|MPH)\s*$",
                      before_chunk, re.IGNORECASE):
            return True  # author affiliation marker

    # Heuristic 5: Table-of-contents page numbers
    # e.g., ". . . . . . . . 7 METHODS . . ."
    if num < 200:
        before_dots = text[max(0, start - 15):start]
        if re.search(r"\.[\s.]{4,}$", before_dots):
            return True  # TOC page number

    # Heuristic 6: FDA section cross-references in parentheses
    # e.g., "(4)", "(4, 5.2)", "(7)" in PI documents
    if num < 20 and start >= 1 and text[start - 1] == "(":
        after_close = text[end:min(len(text), end + 5)]
        if re.match(r"\s*[,).]", after_close):
            # Check it's NOT n=(12) or (n=4) which IS clinical data
            paren_before = text[max(0, start - 5):start]
            if not re.search(r"[n=]", paren_before, re.IGNORECASE):
                return True  # section cross-reference

    return False

def extract_numeric_tokens(text: str) -> List[NumericToken]:
    """Extract all numeric tokens with their surrounding context.

    Unlike the old pipeline which stored bare numbers ["32.6", "24"],
    this stores context-augmented tokens like:
      NumericToken(raw="32.6%", context="achieved 32.6% continuous abstinence")

    This enables the LLM Judge to verify WHAT each number refers to
    per Section 4.1 (Exact Figure Traceability).

    Args:
        text: Normalized text from a document chunk.

    Returns:
        List of NumericToken objects with context.
    """
    if not text:
        return []

    tokens = []
    seen_positions = set()

    for match in NUMERIC_PATTERN.finditer(text):
        start, end = match.start(), match.end()
        raw_value = match.group().strip()

        # Skip if we've already captured a number at this position
        # (overlapping regex matches)
        if start in seen_positions:
            continue
        seen_positions.add(start)

        # Skip pure years (1900-2099) when not preceded by units/context
        if re.match(r"^(19|20)\d{2}$", raw_value):
            # Check if it looks like a year in context (not a data value)
            before = text[max(0, start - 10):start].lower()
            if not any(kw in before for kw in ["%", "n=", "mg", "dose", "score", "rate"]):
                continue

        # Skip citation/reference superscript markers
        # These appear in LlamaParser output as:
        #   "treatment.10,11"  (refs glued to preceding word)
        #   "condition.A1,A2"  (letter-number citation codes)
        #   "weakness.3,4,5"   (comma-separated bare ref numbers)
        if _is_citation_marker(text, raw_value, start, end):
            continue

        # Extract context window
        ctx_start = max(0, start - CONTEXT_WINDOW)
        ctx_end = min(len(text), end + CONTEXT_WINDOW)
        context = text[ctx_start:ctx_end].strip()

        tokens.append(NumericToken(
            raw_value=raw_value,
            normalized_value=normalize_numeric_value(raw_value),
            context=context,
            start_pos=start,
            end_pos=end,
        ))

    return tokens


def extract_numeric_strings(text: str) -> List[str]:
    """Convenience: extract just the contextualized string representations.

    Returns strings like "32.6% (context: achieved 32.6% continuous abstinence)"
    for storage in the vector database payload.
    """
    tokens = extract_numeric_tokens(text)
    return [t.normalized_value for t in tokens]


def extract_numeric_contexts(text: str) -> List[str]:
    """Extract context-augmented numeric strings for storage.

    Returns: ["achieved 32.6% continuous abstinence rate at", ...]
    These are stored in the vector DB and used by the LLM Judge
    to verify what each number refers to.
    """
    tokens = extract_numeric_tokens(text)
    return [t.context for t in tokens]


# ---------------------------------------------------------------------------
# Numeric value normalization
# ---------------------------------------------------------------------------

def normalize_numeric_value(token: str) -> str:
    """Normalize a single numeric token for consistent comparison.

    Handles:
    - "32.6 %" → "32.6%"
    - "p < 0.001" → "p<0.001"
    - "p < .001" → "p<0.001"
    - "32·6%" → "32.6%" (already handled by normalize_unicode)
    """
    t = token.strip()
    # Remove spaces around operators
    t = re.sub(r"\s*([<>=≤≥:=])\s*", r"\1", t)
    # Remove space before %
    t = re.sub(r"\s+%", "%", t)
    # Normalize ".001" to "0.001" after operators
    t = re.sub(r"(?<=[<>=≤≥])\.(\d)", r"0.\1", t)
    return t.lower()


def check_numeric_match(
    claim_value: str,
    evidence_value: str,
    tolerance_pct: float = 2.0,
) -> bool:
    """Check if two numeric values match within rounding tolerance.

    Per Section 4.2: ±2 percentage points is generally permissible.
    Beyond ±5 percentage points requires explicit justification.
    """
    try:
        claim_num = float(re.sub(r"[^0-9.]", "", claim_value))
        evidence_num = float(re.sub(r"[^0-9.]", "", evidence_value))
        return abs(claim_num - evidence_num) <= tolerance_pct
    except (ValueError, TypeError):
        return False
