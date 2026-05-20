"""CT→RT Mapping Matrix — parsed from Claim-to-Reference_Mapping.md.

Step 2 of the pipeline: given a CT-ID, returns which RT-IDs are
Primary (P), Acceptable (A), Conditional (C), or Not Acceptable (N).

This is deterministic code, NOT an LLM call.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from ..schemas import EvidenceTier, TierMapping

logger = logging.getLogger(__name__)


class MappingMatrix:
    """Lookup table for CT-ID → RT-ID tier mappings.

    Parses the Claim-to-Reference_Mapping.md file into an in-memory
    dictionary for fast lookup during retrieval.
    """

    def __init__(self, mapping_path: Optional[Path] = None):
        # ct_id -> list of TierMapping
        self._matrix: Dict[str, List[TierMapping]] = {}

        if mapping_path and mapping_path.exists():
            self._parse_mapping_file(mapping_path)
            logger.info(
                f"Loaded mapping matrix: {len(self._matrix)} claim types, "
                f"{sum(len(v) for v in self._matrix.values())} total mappings"
            )
        else:
            logger.warning("No mapping file found — all RT-IDs will be treated equally")

    def _parse_mapping_file(self, path: Path) -> None:
        """Parse the markdown mapping file into the internal matrix.

        Expected format per claim type section:
        ### CT-XXX — Description
        | RT-ID | Ref. Cat. | Reference Type | Tier | Note |
        |---|---|---|---|---|
        | RT-101 | B1 | US Prescribing Information | P | Primary source |
        """
        content = path.read_text(encoding="utf-8")
        lines = content.split("\n")

        current_ct_id = None
        in_table = False

        for line in lines:
            line = line.strip()

            # Detect claim type header: ### CT-XXX — Description
            ct_match = re.match(r"###\s+(CT-[A-Z]?\d+)\s*[—–-]", line)
            if ct_match:
                current_ct_id = ct_match.group(1)
                self._matrix[current_ct_id] = []
                in_table = False
                continue

            # Detect table separator (the |---|---|... line)
            if current_ct_id and re.match(r"\|[-\s|]+\|$", line):
                in_table = True
                continue

            # Parse table rows
            if current_ct_id and in_table and line.startswith("|"):
                cells = [c.strip() for c in line.split("|")]
                # Filter empty cells from leading/trailing |
                cells = [c for c in cells if c]

                if len(cells) >= 4:
                    rt_id = cells[0].strip()
                    tier_str = cells[3].strip().upper()
                    note = cells[4].strip() if len(cells) > 4 else ""

                    # Map tier string to enum
                    tier_map = {"P": EvidenceTier.PRIMARY, "A": EvidenceTier.ACCEPTABLE,
                                "C": EvidenceTier.CONDITIONAL, "N": EvidenceTier.NOT_ACCEPTABLE}
                    tier = tier_map.get(tier_str)

                    if tier and rt_id.startswith("RT-"):
                        self._matrix[current_ct_id].append(
                            TierMapping(rt_id=rt_id, tier=tier, note=note)
                        )

            # End of table
            if current_ct_id and in_table and not line.startswith("|") and line:
                in_table = False

    def get_tiers(self, ct_id: str) -> List[TierMapping]:
        """Get all RT-ID tier mappings for a given claim type.

        Args:
            ct_id: Claim type ID (e.g., "CT-201").

        Returns:
            List of TierMapping objects.
        """
        return self._matrix.get(ct_id, [])

    def has_ct_id(self, ct_id: str) -> bool:
        """Check whether a CT-ID exists in the mapping matrix."""
        return ct_id in self._matrix

    def get_primary_rt_ids(self, ct_id: str) -> Set[str]:
        """Get RT-IDs that are Primary (Tier P) for this claim type."""
        return {m.rt_id for m in self.get_tiers(ct_id) if m.tier == EvidenceTier.PRIMARY}

    def get_acceptable_rt_ids(self, ct_id: str) -> Set[str]:
        """Get RT-IDs that are Acceptable (Tier A)."""
        return {m.rt_id for m in self.get_tiers(ct_id) if m.tier == EvidenceTier.ACCEPTABLE}

    def get_conditional_rt_ids(self, ct_id: str) -> Set[str]:
        """Get RT-IDs that are Conditional (Tier C)."""
        return {m.rt_id for m in self.get_tiers(ct_id) if m.tier == EvidenceTier.CONDITIONAL}

    def get_blocked_rt_ids(self, ct_id: str) -> Set[str]:
        """Get RT-IDs that are Not Acceptable (Tier N) — hard blocked."""
        return {m.rt_id for m in self.get_tiers(ct_id) if m.tier == EvidenceTier.NOT_ACCEPTABLE}

    def get_allowed_rt_ids(self, ct_id: str) -> Set[str]:
        """Get all RT-IDs that are NOT blocked (P + A + C)."""
        return {
            m.rt_id for m in self.get_tiers(ct_id)
            if m.tier != EvidenceTier.NOT_ACCEPTABLE
        }
