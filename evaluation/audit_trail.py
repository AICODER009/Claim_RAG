"""Audit Trail — immutable record of every substantiation decision.

Step 6 of the pipeline: logs the complete decision chain to satisfy
Section 8 (Process, Auditability and Governance) of the requirements.

This is CODE (database writes), not an LLM.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..schemas import (
    AuditRecord,
    CitationMetadata,
    ClaimClassification,
    CoverageResult,
    CoverageVerdict,
    PICOTComponents,
)

logger = logging.getLogger(__name__)


class AuditTrail:
    """Creates and stores immutable audit records for MLR compliance."""

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize audit trail.

        Args:
            output_dir: Directory to store audit records as JSON.
                       If None, records are only returned (not persisted).
        """
        self.output_dir = output_dir
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)

    def create_record(
        self,
        claim_text: str,
        classification: ClaimClassification,
        picot: PICOTComponents,
        coverage_result: CoverageResult,
        logic_gate_output: Dict,
        evidence_passages: List[Dict],
    ) -> AuditRecord:
        """Create a complete audit record for one claim substantiation.

        This record contains everything required by Section 8.1
        (Citation Metadata Schema) and Section 8.2 (Audit Trail).

        Args:
            claim_text: The original claim.
            classification: CT-ID classification.
            picot: PICOT components.
            coverage_result: Judge evaluation result.
            logic_gate_output: Logic gate verdict + flags.
            evidence_passages: Retrieved evidence with metadata.

        Returns:
            Complete AuditRecord.
        """
        # Build citation metadata for each evidence passage (Section 8.1)
        citations = []
        for passage in evidence_passages:
            citation = CitationMetadata(
                # Mandatory fields
                full_citation=self._build_full_citation(passage),
                file_name=passage.get("ref_id", "unknown") + ".pdf",
                page_number=passage.get("page", 0),
                verbatim_anchor_text=passage.get("text", ""),
                # Conditional fields
                doi=passage.get("doc_metadata", {}).get("doi") if passage.get("doc_metadata") else None,
                section_heading=passage.get("section"),
                sentence_index=passage.get("sentence_number"),
                table_figure_number=passage.get("source"),
                # Data on File label for CSR documents (RT-209)
                data_on_file_label=passage.get("rt_id") == "RT-209",
                # Preliminary data flag for conference posters (RT-402)
                preliminary_data_flag=passage.get("rt_id") == "RT-402",
            )
            citations.append(citation)

        # Determine verdict enum
        verdict_str = logic_gate_output.get("verdict", "block")
        verdict = CoverageVerdict(verdict_str)

        record = AuditRecord(
            claim_text=claim_text,
            claim_ct_id=classification.ct_id,
            classification=classification,
            picot=picot,
            retrieved_citations=citations,
            evidence_rt_ids=[p.get("rt_id", "") for p in evidence_passages],
            coverage_result=coverage_result,
            verdict=verdict,
            fair_balance_linked="fair balance" not in " ".join(
                logic_gate_output.get("flags", [])
            ).lower(),
            secondary_citation_flag=logic_gate_output.get("secondary_citation", False),
            timestamp=datetime.utcnow(),
        )

        # Persist to disk if output_dir is set
        if self.output_dir:
            self._save_record(record)

        logger.info(
            f"Audit record created: {record.verdict.value} "
            f"(CT={record.claim_ct_id}, score={record.coverage_result.coverage_score:.0f})"
        )

        return record

    def _save_record(self, record: AuditRecord) -> None:
        """Save audit record as a JSON file."""
        timestamp = record.timestamp.strftime("%Y%m%d_%H%M%S_%f")
        filename = f"audit_{record.claim_ct_id}_{timestamp}.json"
        filepath = self.output_dir / filename

        filepath.write_text(
            record.model_dump_json(indent=2),
            encoding="utf-8",
        )
        logger.debug(f"Audit record saved to {filepath}")

    @staticmethod
    def _build_full_citation(passage: Dict) -> str:
        """Build a full citation string from passage metadata.

        Format: "Author(s). Title. Journal Year;Volume:Pages."
        """
        meta = passage.get("doc_metadata", {}) or {}
        parts = []

        authors = meta.get("authors")
        if authors:
            if isinstance(authors, list):
                parts.append(", ".join(authors[:3]))
                if len(authors) > 3:
                    parts[-1] += " et al."
            else:
                parts.append(str(authors))

        title = meta.get("title") or passage.get("ref_title", "")
        if title:
            parts.append(title)

        journal = meta.get("journal_name", "")
        year = meta.get("year", "")
        if journal and year:
            parts.append(f"{journal} {year}")
        elif year:
            parts.append(str(year))

        doi = meta.get("doi", "")
        if doi:
            parts.append(f"doi:{doi}")

        return ". ".join(parts) + "." if parts else passage.get("ref_id", "Unknown")
