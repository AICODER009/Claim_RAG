"""CT→RT Mapping Matrix — parsed from Claim-to-Reference_Mapping.md.

Step 2 of the pipeline: given a CT-ID, returns which RT-IDs are
Primary (P), Acceptable (A), Conditional (C), or Not Acceptable (N).

Aligned with categorization_new/ (pre-2026-05-20):
  - A10 = Off-Label / Scientific-Exchange (CT-B01–CT-B04)  [was A11]
  - A11 = Study Design / Methodology  (CT-D01–CT-D06)      [brand new]
  - Evidence-type modifiers (CT-A01–CT-A08) still in A10 of Claim Attributes
  - RT-602 is DEPRECATED — merged into RT-601

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

    # CT-IDs that have no reference mapping yet (pending assignment)
    # CT-D01–CT-D06 were added to the classification taxonomy on 2026-05-08
    # but the Mapping file has not yet assigned RT-IDs to them.
    PENDING_MAPPING_CT_IDS: set = {
        "CT-D01", "CT-D02", "CT-D03", "CT-D04", "CT-D05", "CT-D06",
    }

    # CT-IDs that are evidence-type MODIFIERS — must always be paired with a primary CT.
    # From Claim Attributes sheet: Is Modifier? = Yes
    MODIFIER_CT_IDS: set = {
        "CT-204",   # Subgroup efficacy
        "CT-A01",   # RWE
        "CT-A02",   # Meta-analysis / systematic review
        "CT-A03",   # Network meta-analysis
        "CT-A04",   # Pooled analysis (integrated)
        "CT-A05",   # Registry-based
        "CT-A06",   # Observational (cohort / case-control)
        "CT-A07",   # Pragmatic-trial
        "CT-A08",   # Single-arm / uncontrolled
    }

    # Audience restrictions from Claim Attributes sheet (payer-only CT-IDs)
    PAYER_ONLY_CT_IDS: set = {
        "CT-405",   # Indirect / cross-trial comparison (PAAB disallows for HCP)
        "CT-901", "CT-902", "CT-903", "CT-904", "CT-905",
        "CT-906", "CT-907", "CT-908", "CT-909",   # HCEI A9
        "CT-B02",   # Pre-approval information exchange (PIE) — payer only
        "CT-B03",   # HCEI off-label-related — payer only
    }
    HCP_ONLY_CT_IDS: set = {
        "CT-B01",   # SIUU communication — HCP only (with disclosures)
        "CT-B04",   # Scientific-exchange — HCP unsolicited only
    }

    # RT-602 is DEPRECATED (merged into RT-601) — any reference to RT-602 should
    # be treated as RT-601 during retrieval. Retained for ID stability.
    DEPRECATED_RT_IDS: dict = {"RT-602": "RT-601"}

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

        Supports TWO formats:

        Format A — old grouped-per-claim (used by original mapping md):
          ### CT-XXX — Description
          | RT-ID | Ref. Cat. | Reference Type | Tier | Note |

        Format B — new flat long-form table (categorization_new/ pre-2026-05-20):
          ## Sheet: Mapping (Long)
          | CT-ID | Claim Group | Claim Type | RT-ID | Reference Category | Reference Type | Tier | Note |
        """
        content = path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # ── Detect format ──────────────────────────────────────────────────────
        is_flat_format = any(
            "Sheet: Mapping (Long)" in line or
            ("| CT-ID |" in line and "| Claim Group |" in line)
            for line in lines
        )

        if is_flat_format:
            self._parse_flat_format(lines)
        else:
            self._parse_grouped_format(lines)

        # Warn about CT-D types with no mapping yet
        for ct_id in self.PENDING_MAPPING_CT_IDS:
            if ct_id not in self._matrix:
                logger.warning(
                    f"CT-ID '{ct_id}' (Study Design / Methodology) has no reference "
                    f"mapping yet — substantiation engine will return empty results. "
                    f"Assign RT-IDs in the mapping file when available."
                )

    def _parse_flat_format(self, lines: list) -> None:
        """Parse new flat long-form table: CT-ID | Claim Group | Claim Type | RT-ID | ... | Tier | Note."""
        in_mapping_section = False
        header_found = False

        for line in lines:
            line = line.strip()

            # Detect start of Mapping (Long) section
            if "Sheet: Mapping (Long)" in line:
                in_mapping_section = True
                header_found = False
                continue

            # Stop at next sheet
            if in_mapping_section and line.startswith("## Sheet:") and "Mapping (Long)" not in line:
                break

            if not in_mapping_section:
                continue

            # Skip separator and detect header
            if re.match(r"\|[-\s|]+\|$", line):
                header_found = True
                continue

            # Parse data rows
            if header_found and line.startswith("|"):
                cells = [c.strip() for c in line.split("|")]
                cells = [c for c in cells if c]  # remove empty

                # Expected: CT-ID | Claim Group | Claim Type | RT-ID | Ref Category | Ref Type | Tier | Note
                if len(cells) >= 7:
                    ct_id = cells[0].strip()
                    rt_id = cells[3].strip()
                    tier_str = cells[6].strip().upper()
                    note = cells[7].strip() if len(cells) > 7 else ""

                    # Resolve deprecated RT-IDs
                    rt_id = self.DEPRECATED_RT_IDS.get(rt_id, rt_id)

                    tier_map = {
                        "P": EvidenceTier.PRIMARY,
                        "A": EvidenceTier.ACCEPTABLE,
                        "C": EvidenceTier.CONDITIONAL,
                        "N": EvidenceTier.NOT_ACCEPTABLE,
                    }
                    tier = tier_map.get(tier_str)

                    if tier and ct_id.startswith("CT-") and rt_id.startswith("RT-"):
                        if ct_id not in self._matrix:
                            self._matrix[ct_id] = []
                        self._matrix[ct_id].append(
                            TierMapping(rt_id=rt_id, tier=tier, note=note)
                        )

    def _parse_grouped_format(self, lines: list) -> None:
        """Parse old grouped-per-claim format: ### CT-XXX — Description + per-claim tables."""
        current_ct_id = None
        in_table = False

        for line in lines:
            line = line.strip()

            # Detect claim type header: ### CT-XXX — Description
            # Supports alphanumeric IDs: CT-101, CT-A01, CT-B01, CT-D01
            ct_match = re.match(r"###\s+(CT-[A-Z0-9]+(?:-[A-Z0-9]+)?)\s*[—\-–]", line)
            if ct_match:
                current_ct_id = ct_match.group(1)
                self._matrix.setdefault(current_ct_id, [])
                in_table = False
                continue

            # Detect table separator
            if current_ct_id and re.match(r"\|[-\s|]+\|$", line):
                in_table = True
                continue

            # Parse table rows
            if current_ct_id and in_table and line.startswith("|"):
                cells = [c.strip() for c in line.split("|")]
                cells = [c for c in cells if c]

                if len(cells) >= 4:
                    rt_id = cells[0].strip()
                    tier_str = cells[3].strip().upper()
                    note = cells[4].strip() if len(cells) > 4 else ""

                    # Resolve deprecated RT-IDs
                    rt_id = self.DEPRECATED_RT_IDS.get(rt_id, rt_id)

                    tier_map = {
                        "P": EvidenceTier.PRIMARY,
                        "A": EvidenceTier.ACCEPTABLE,
                        "C": EvidenceTier.CONDITIONAL,
                        "N": EvidenceTier.NOT_ACCEPTABLE,
                    }
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

    def is_modifier(self, ct_id: str) -> bool:
        """Return True if this CT-ID is an evidence-type modifier (must pair with primary)."""
        return ct_id in self.MODIFIER_CT_IDS

    def is_pending_mapping(self, ct_id: str) -> bool:
        """Return True if this CT-ID has no reference mapping yet (CT-D01–CT-D06)."""
        return ct_id in self.PENDING_MAPPING_CT_IDS

    def get_audience(self, ct_id: str) -> str:
        """Return audience constraint: 'payer_only', 'hcp_only', or 'unrestricted'."""
        if ct_id in self.PAYER_ONLY_CT_IDS:
            return "payer_only"
        if ct_id in self.HCP_ONLY_CT_IDS:
            return "hcp_only"
        return "unrestricted"

    def resolve_deprecated_rt(self, rt_id: str) -> str:
        """Resolve a deprecated RT-ID to its replacement (e.g. RT-602 → RT-601)."""
        return self.DEPRECATED_RT_IDS.get(rt_id, rt_id)

    def get_zero_p_tier_ct_ids(self) -> Set[str]:
        """Return CT-IDs that have no P-tier references (CT-203, CT-204, CT-607, CT-806, CT-807).

        For these, the engine should never expect a P-tier result.
        From Preferred Cheat Sheet: count of P = 0.
        """
        return {
            ct_id for ct_id, tiers in self._matrix.items()
            if not any(m.tier == EvidenceTier.PRIMARY for m in tiers)
        }
