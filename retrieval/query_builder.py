"""Query Builder — Qdrant vector search with RT-ID tier filtering.

Steps 2-3 of the pipeline:
1. Takes the classified CT-ID, looks up the mapping matrix
2. Encodes the claim question via MedCPT Query Encoder
3. Executes Qdrant search with tier-based boost/filter
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set

import numpy as np
from qdrant_client import QdrantClient, models

from ..schemas import EvidenceTier
from .mapping_matrix import MappingMatrix

logger = logging.getLogger(__name__)


class QueryBuilder:
    """Build and execute Qdrant vector search with MLR tier filtering."""

    def __init__(
        self,
        qdrant_client: QdrantClient,
        collection_name: str,
        mapping_matrix: MappingMatrix,
        tier_p_boost: float = 2.0,
        tier_a_boost: float = 1.0,
        tier_c_boost: float = 0.5,
    ):
        self._client = qdrant_client
        self._collection = collection_name
        self._matrix = mapping_matrix
        self._boosts = {
            EvidenceTier.PRIMARY: tier_p_boost,
            EvidenceTier.ACCEPTABLE: tier_a_boost,
            EvidenceTier.CONDITIONAL: tier_c_boost,
        }

    def search(
        self,
        query_vector: List[float],
        ct_id: Optional[str] = None,
        ref_id_filter: Optional[str] = None,
        rt_id_filter: Optional[Set[str]] = None,
        top_k: int = 50,
    ) -> List[Dict]:
        """Execute a vector search with optional MLR tier filtering.

        Args:
            query_vector: MedCPT query embedding (768-dim).
            ct_id: Classified claim type ID (enables tier filtering).
            ref_id_filter: Optional — scope to a specific document.
            rt_id_filter: Optional — explicit RT-ID whitelist.
            top_k: Number of candidates to retrieve.

        Returns:
            List of result dicts sorted by boosted score.
        """
        # Determine tier sets from mapping matrix
        if ct_id and self._matrix.has_ct_id(ct_id):
            blocked_rt_ids = self._matrix.get_blocked_rt_ids(ct_id)
            primary_rt_ids = self._matrix.get_primary_rt_ids(ct_id)
            acceptable_rt_ids = self._matrix.get_acceptable_rt_ids(ct_id)
            conditional_rt_ids = self._matrix.get_conditional_rt_ids(ct_id)
            logger.info(
                f"Tier filter for {ct_id}: "
                f"P={len(primary_rt_ids)}, A={len(acceptable_rt_ids)}, "
                f"C={len(conditional_rt_ids)}, N(blocked)={len(blocked_rt_ids)}"
            )
        else:
            blocked_rt_ids = set()
            primary_rt_ids = set()
            acceptable_rt_ids = set()
            conditional_rt_ids = set()
            if ct_id:
                logger.warning(f"CT-ID '{ct_id}' not found in matrix — no tier filtering")

        # Build Qdrant filter conditions
        must_conditions = []
        must_not_conditions = []

        # Scope to specific document if requested
        if ref_id_filter:
            must_conditions.append(
                models.FieldCondition(
                    key="ref_id",
                    match=models.MatchValue(value=ref_id_filter),
                )
            )

        # Explicit RT-ID whitelist
        if rt_id_filter:
            must_conditions.append(
                models.FieldCondition(
                    key="rt_id",
                    match=models.MatchAny(any=list(rt_id_filter)),
                )
            )

        # Block Not Acceptable RT-IDs
        if blocked_rt_ids:
            must_not_conditions.append(
                models.FieldCondition(
                    key="rt_id",
                    match=models.MatchAny(any=list(blocked_rt_ids)),
                )
            )

        # Note: All points in Qdrant are already embeddable
        # (non-embeddable chunks are not uploaded by run_qdrant_upload.py)

        query_filter = models.Filter(
            must=must_conditions if must_conditions else None,
            must_not=must_not_conditions if must_not_conditions else None,
        )

        # Execute Qdrant vector search
        results = self._client.query_points(
            collection_name=self._collection,
            query=query_vector,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )

        # Apply tier-based score boosting
        boosted_results = []
        for point in results.points:
            payload = point.payload or {}
            rt_id = payload.get("rt_id", "")
            raw_score = point.score or 0.0

            # Determine boost multiplier
            if rt_id in primary_rt_ids:
                boost = self._boosts[EvidenceTier.PRIMARY]
            elif rt_id in acceptable_rt_ids:
                boost = self._boosts[EvidenceTier.ACCEPTABLE]
            elif rt_id in conditional_rt_ids:
                boost = self._boosts[EvidenceTier.CONDITIONAL]
            else:
                boost = 0.5  # Unknown/unclassified RT-ID

            boosted_score = raw_score * (1.0 + boost)

            boosted_results.append({
                "id": point.id,
                "score": round(raw_score, 4),
                "boosted_score": round(boosted_score, 4),
                "rt_id": rt_id,
                "tier": self._get_tier_label(
                    rt_id, primary_rt_ids, acceptable_rt_ids, conditional_rt_ids
                ),
                "text": payload.get("text", ""),
                "ref_id": payload.get("ref_id", ""),
                "section": payload.get("section", ""),
                "segment_type": payload.get("segment_type", ""),
                "sent_id": payload.get("sent_id", ""),
                "doc_metadata": payload.get("doc_metadata", {}),
                "numeric_tokens": payload.get("numeric_tokens", []),
                "ref_category": payload.get("ref_category", ""),
                "reference_type_name": payload.get("reference_type_name", ""),
            })

        # Sort by boosted score
        boosted_results.sort(key=lambda x: x["boosted_score"], reverse=True)
        return boosted_results

    @staticmethod
    def _get_tier_label(
        rt_id: str,
        primary: Set[str],
        acceptable: Set[str],
        conditional: Set[str],
    ) -> str:
        if rt_id in primary:
            return "P"
        if rt_id in acceptable:
            return "A"
        if rt_id in conditional:
            return "C"
        return "?"
