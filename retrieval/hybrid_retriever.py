"""Hybrid Retriever — Qdrant dense + BM25 sparse search with RRF fusion.

Combines TWO retrieval signals:
  1. Dense: MedCPT query vector → cosine similarity (semantic matching)
  2. BM25:  Sparse vector search via separate collection → TF-IDF scoring (lexical matching)
  3. Fuse:  Reciprocal Rank Fusion (RRF) merges both ranked lists
  4. Re-rank: Cross-encoder scores (original_claim, passage) pairs for precision

RRF formula: score(d) = Σ 1/(k + rank_i(d))
  where k=60 (standard constant), rank_i = position in ranked list i

After RRF fusion, cross-encoder re-ranking uses the original claim text (with
exact numbers/terms) to score each candidate. This catches passages with matching
numeric values that bi-encoder dense search misses.

Finally, tier-based boosting from the Mapping Matrix is applied:
  - Primary (P) sources → 2x boost
  - Acceptable (A) sources → 1x (no boost)
  - Conditional (C) sources → 0.5x penalty
  - Not Acceptable (N) → hard-blocked before retrieval

This replaces the single-signal dense-only retrieval in query_builder.py.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Dict, List, Optional, Set

from qdrant_client import QdrantClient, models

from ..schemas import EvidenceTier
from .mapping_matrix import MappingMatrix

logger = logging.getLogger(__name__)

# RRF constant — standard value from the original RRF paper (Cormack et al.)
RRF_K = 60

# CT-IDs where the Prescribing Information (RT-101) is NOT the highest-authority
# source per the Claim-to-Reference Mapping Matrix. For these claim types the
# product boost is suppressed so trial papers (RT-301) and ISS (RT-212) can
# compete fairly for top slots.
# Derived from: Claim-to-Reference_Mapping.md — read the Primary tier column.
CT_ID_PI_NOT_PRIMARY: set = {
    # A2 Efficacy — PI is Acceptable (A); pivotal trial is Primary (P)
    "CT-201",  # Primary-endpoint efficacy
    "CT-202",  # Secondary-endpoint efficacy
    "CT-203",  # Exploratory / post-hoc endpoint  (PI is N)
    "CT-204",  # Subgroup efficacy               (PI is A)
    "CT-205",  # Onset-of-action
    "CT-206",  # Durability / duration-of-effect
    "CT-207",  # Magnitude-of-effect             (PI is A)
    "CT-208",  # Response-rate / responder
    "CT-209",  # Time-to-event / survival
    # A3 Safety — PI is Primary but ISS/trial pub also primary; suppress
    # boost when granular per-AE % not in PI (trial paper has it)
    "CT-301",  # Adverse-event / AE-profile
    "CT-302",  # Tolerability
    "CT-303",  # Comparative safety              (PI is N)
    "CT-310",  # Immunogenicity
    # A4 Comparative
    "CT-401",  # Superiority                     (PI is N)
    "CT-402",  # Non-inferiority
    "CT-403",  # Clinical equivalence
    "CT-404",  # Head-to-head
    # A8 Outcomes — trial paper is co-primary with PI
    "CT-801",  # Patient-reported outcome (PRO)
    "CT-802",  # HRQoL
    "CT-803",  # Functional-status / ADL
    "CT-804",  # Symptom-relief
}


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract meaningful search keywords from a claim/question.

    Filters out common English stopwords and short tokens.
    Keeps medical terms, drug names, and numeric values.
    """
    STOPWORDS = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "dare", "ought",
        "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "out", "off", "over", "under", "again",
        "further", "then", "once", "here", "there", "when", "where",
        "why", "how", "all", "each", "every", "both", "few", "more",
        "most", "other", "some", "such", "no", "nor", "not", "only",
        "own", "same", "so", "than", "too", "very", "just", "because",
        "but", "and", "or", "if", "while", "that", "this", "what",
        "which", "who", "whom", "these", "those", "it", "its",
    }

    # Tokenize: split on non-alphanumeric (keep dots for numbers like 32.6%)
    tokens = re.findall(r"[a-zA-Z0-9]+(?:\.[0-9]+)?%?", text.lower())

    # Filter stopwords and short tokens
    keywords = [t for t in tokens if t not in STOPWORDS and len(t) >= 2]

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique.append(kw)

    return unique[:max_keywords]


class HybridRetriever:
    """Qdrant hybrid retrieval with RRF fusion and tier boosting."""

    def __init__(
        self,
        qdrant_client: QdrantClient,
        collection_name: str,
        mapping_matrix: MappingMatrix,
        bm25_collection: Optional[str] = None,
        bm25_model: object = None,
        tier_p_boost: float = 2.0,
        tier_a_boost: float = 1.0,
        tier_c_boost: float = 0.5,
        dense_weight: float = 0.7,
        text_weight: float = 0.3,
    ):
        self._client = qdrant_client
        self._collection = collection_name
        self._bm25_collection = bm25_collection or f"{collection_name}_bm25"
        self._bm25_model = bm25_model  # fastembed Bm25 instance
        self._matrix = mapping_matrix
        self._boosts = {
            EvidenceTier.PRIMARY: tier_p_boost,
            EvidenceTier.ACCEPTABLE: tier_a_boost,
            EvidenceTier.CONDITIONAL: tier_c_boost,
        }
        self._dense_weight = dense_weight
        self._text_weight = text_weight
        self._cross_encoder = None  # Lazily loaded
        self._cross_encoder_model = os.getenv(
            "CROSS_ENCODER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )

    def search(
        self,
        query_vector: List[float],
        query_text: str,
        ct_id: Optional[str] = None,
        ref_id_filter: Optional[str] = None,
        rt_id_filter: Optional[Set[str]] = None,
        exclude_ref_ids: Optional[Set[str]] = None,
        original_claim_text: Optional[str] = None,
        keyword_source_text: Optional[str] = None,
        bm25_query_text: Optional[str] = None,
        dense_top_k: int = 150,
        text_top_k: int = 100,
        final_top_k: int = 50,
    ) -> List[Dict]:
        """Execute hybrid search: dense + BM25 sparse with RRF fusion.

        Args:
            query_vector: MedCPT query embedding (768-dim).
            query_text: The rewritten question (for dense search).
            original_claim_text: Original claim text for cross-encoder reranking.
            keyword_source_text: Original claim text for keyword extraction (fallback).
            bm25_query_text: Text to use for BM25 query (typically the original claim).
                If None, falls back to keyword_source_text or query_text.
            ct_id: Classified claim type ID (enables tier filtering).
            ref_id_filter: Optional — scope to a specific document.
            rt_id_filter: Optional — explicit RT-ID whitelist.
            exclude_ref_ids: Optional — ref_ids to exclude (competitor drugs).
            dense_top_k: Candidates from dense retrieval.
            text_top_k: Candidates from BM25 retrieval.
            final_top_k: Final results after RRF fusion (no cross-encoder).

        Returns:
            List of result dicts sorted by RRF-fused + tier-boosted score.
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

        # Build common filter conditions
        base_filter = self._build_filter(
            blocked_rt_ids, ref_id_filter, rt_id_filter, exclude_ref_ids
        )

        # Pre-compute CT-ID flags used across multiple stages below
        _ct_id_upper = (ct_id or "").upper().strip()
        _pi_is_not_primary = _ct_id_upper in CT_ID_PI_NOT_PRIMARY
        claim_source = bm25_query_text or keyword_source_text or query_text

        # --- Signal 1: Dense vector search (MedCPT) ---
        dense_results = self._dense_search(query_vector, base_filter, dense_top_k)
        logger.info(f"Dense search: {len(dense_results)} candidates")

        # --- Signal 2: BM25 sparse search (separate collection) ---
        # Use original claim text for BM25 (preserves exact terms like 'freeze', 'soap')
        bm25_text = bm25_query_text or keyword_source_text or query_text
        if self._bm25_model:
            text_results = self._bm25_search(bm25_text, base_filter, text_top_k)
            logger.info(f"BM25 search: {len(text_results)} candidates")
        else:
            # Fallback: old keyword-based MatchText search
            keywords = extract_keywords(query_text)
            extra_source = keyword_source_text or original_claim_text
            if extra_source:
                claim_keywords = extract_keywords(extra_source, max_keywords=30)
                seen = set(keywords)
                for kw in claim_keywords:
                    if kw not in seen:
                        keywords.append(kw)
                        seen.add(kw)
            if keywords:
                text_results = self._text_search(keywords, base_filter, text_top_k)
                logger.info(f"Text search ({len(keywords)} keywords): {len(text_results)} candidates")
            else:
                text_results = []
                logger.warning("No BM25 model and no keywords — text search skipped")

        # --- Signal 3: Exact claim-phrase AND-match search ---
        # Searches for chunks containing ALL distinctive claim terms at once.
        #
        # Brand-name auto-strip (ONLY for trial-primary CT-IDs):
        # Trial papers use INNs ("efgartigimod PH20"), not brand names ("VYVGART
        # Hytrulo"). If brand-name keywords stay in AND-match, the search returns
        # 0 results because no trial-paper chunk contains the brand name AND the
        # clinical data in the same passage.
        #
        # GUARD: We only strip brand names when the CT-ID is in CT_ID_PI_NOT_PRIMARY
        # (i.e. trial papers are the authoritative source). For PI-primary CTs like
        # CT-606 storage or CT-601 dosing, brand names STAY in AND-match so the
        # search correctly scopes to the right product's PI. This ensures previously
        # passing PI-primary claims are not affected.
        claim_for_exact = bm25_query_text or keyword_source_text or original_claim_text or query_text
        exact_keywords = extract_keywords(claim_for_exact, max_keywords=30)
        if exact_keywords and dense_results and _ct_id_upper in CT_ID_PI_NOT_PRIMARY:
            brand_names = self._detect_brand_names(claim_for_exact, dense_results + text_results)
            if brand_names:
                pre_count = len(exact_keywords)
                exact_keywords = [kw for kw in exact_keywords if kw.lower() not in brand_names]
                logger.info(
                    f"AND-match: auto-stripped {pre_count - len(exact_keywords)} brand-name "
                    f"keyword(s) {brand_names} (CT-ID={_ct_id_upper}, trial-primary) "
                    f"— trial papers use INNs not brand names"
                )
        exact_results = self._and_match_search(exact_keywords, base_filter, min(text_top_k, 50)) if exact_keywords else []
        if exact_results:
            logger.info(f"Exact AND-match search: {len(exact_results)} candidates")

        # --- RRF Fusion (3 signals) ---
        fused = self._rrf_fuse_3(dense_results, text_results, exact_results)
        logger.info(f"RRF fusion: {len(fused)} unique documents")

        # --- Tier boosting ---
        boosted = self._apply_tier_boost(
            fused, primary_rt_ids, acceptable_rt_ids, conditional_rt_ids
        )

        # --- Off-product PI penalty (trial-primary CT-IDs only) ---
        # For CT-301/CT-201 etc., a Gamunex or Hizentra PI has ZERO authority
        # over VYVGART ADHERE trial data. After RRF these off-product PIs rank
        # high simply because they contain injection/infection keywords. Apply
        # a 0.3x penalty to RT-101/RT-102 chunks whose ref_id does NOT match
        # any brand name detected in the claim. Trial papers are untouched.
        if _pi_is_not_primary and claim_source:
            brand_names = self._detect_brand_names(claim_source, boosted)
            if brand_names:
                penalised = 0
                for result in boosted:
                    rt = result.get("rt_id", "")
                    ref = result.get("ref_id", "").lower()
                    is_pi = rt in {"RT-101", "RT-102"}
                    is_own_product = any(b in ref for b in brand_names)
                    if is_pi and not is_own_product:
                        result["final_score"] *= 0.3
                        penalised += 1
                if penalised:
                    logger.info(
                        f"Off-product PI penalty: {penalised} chunk(s) penalised "
                        f"(0.3x) — not in brand set {brand_names}"
                    )

        # Cap the number of chunks from any single ref_id before final trim.
        # Prevents one document (e.g. the PI) from monopolising all top slots.
        # max_per_ref_id=5 keeps meaningful depth per source while ensuring
        # diverse evidence reaches the judge.
        boosted = self._apply_diversity_cap(boosted, max_per_ref_id=5)

        # --- Numeric anchor boost (tier-aware) ---
        # AND-match chunks contain ALL claim keywords — but not all are high-quality sources.
        # Only boost AND-match chunks from Primary (P) or Acceptable (A) tier sources,
        # and only if they score above the median (i.e., they're already competitive).
        # This prevents low-tier conference slides / DoF docs from flooding the top positions.
        if exact_results:
            exact_ids = {r.get("id") for r in exact_results}
            scores = [r.get("final_score", 0) for r in boosted]
            median_score = sorted(scores)[len(scores) // 2] if scores else 0
            boosted_count = 0
            for result in boosted:
                if result.get("id") in exact_ids:
                    tier = result.get("tier", "?")
                    if tier in ("P", "A") and result.get("final_score", 0) >= median_score:
                        result["final_score"] *= 1.5  # gentle lift, not a flood
                        boosted_count += 1
            if boosted_count:
                boosted.sort(key=lambda x: x["final_score"], reverse=True)
            logger.info(
                f"Numeric anchor boost: {boosted_count} "
                f"AND-match chunk(s) promoted to top positions"
            )

        # --- Product-name relevance boost (Fix 2 — CT-ID-aware suppression) ---
        # Suppress the boost when the CT-ID indicates the PI is NOT the primary
        # authority for this claim type (per Claim-to-Reference Mapping Matrix).
        # This allows trial papers (RT-301) and ISS (RT-212) to rank fairly.
        if claim_source and not _pi_is_not_primary:
            boosted = self._apply_product_boost(boosted, claim_source)
        elif _pi_is_not_primary:
            # Mark product_boost=False on all results for transparency
            for r in boosted:
                r["product_boost"] = False
            logger.info(
                f"Product boost suppressed for {_ct_id_upper} "
                f"(PI not primary per mapping matrix)"
            )

        # Sort by final score and trim
        boosted.sort(key=lambda x: x["final_score"], reverse=True)
        return boosted[:final_top_k]

    def _build_filter(
        self,
        blocked_rt_ids: Set[str],
        ref_id_filter: Optional[str],
        rt_id_filter: Optional[Set[str]],
        exclude_ref_ids: Optional[Set[str]] = None,
    ) -> models.Filter:
        """Build Qdrant filter conditions shared by both search signals."""
        must_conditions = []
        must_not_conditions = []

        if ref_id_filter:
            must_conditions.append(
                models.FieldCondition(
                    key="ref_id",
                    match=models.MatchValue(value=ref_id_filter),
                )
            )

        if rt_id_filter:
            must_conditions.append(
                models.FieldCondition(
                    key="rt_id",
                    match=models.MatchAny(any=list(rt_id_filter)),
                )
            )

        if blocked_rt_ids:
            must_not_conditions.append(
                models.FieldCondition(
                    key="rt_id",
                    match=models.MatchAny(any=list(blocked_rt_ids)),
                )
            )

        # Exclude competitor drug documents
        if exclude_ref_ids:
            for ref_id in exclude_ref_ids:
                must_not_conditions.append(
                    models.FieldCondition(
                        key="ref_id",
                        match=models.MatchValue(value=ref_id),
                    )
                )

        return models.Filter(
            must=must_conditions if must_conditions else None,
            must_not=must_not_conditions if must_not_conditions else None,
        )

    def _dense_search(
        self,
        query_vector: List[float],
        query_filter: models.Filter,
        top_k: int,
    ) -> List[Dict]:
        """Execute dense vector search via MedCPT cosine similarity."""
        results = self._client.query_points(
            collection_name=self._collection,
            query=query_vector,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )
        return [
            {
                "id": str(point.id),
                "score": point.score or 0.0,
                "payload": point.payload or {},
            }
            for point in results.points
        ]

    def _bm25_search(
        self,
        query_text: str,
        query_filter: models.Filter,
        top_k: int,
    ) -> List[Dict]:
        """Execute BM25 sparse vector search on the BM25 collection.

        Uses fastembed's Qdrant/bm25 tokenizer to convert query text into
        a sparse vector, then searches the BM25 collection for TF-IDF
        scored matches. This provides proper lexical matching with:
          - Built-in stemming (freeze == frozen)
          - IDF scoring (rare terms rank higher)
          - Length normalization
        """
        try:
            # Encode query as sparse vector
            q_vec = list(self._bm25_model.query_embed(query_text))[0]

            results = self._client.query_points(
                collection_name=self._bm25_collection,
                query=models.SparseVector(
                    indices=q_vec.indices.tolist(),
                    values=q_vec.values.tolist(),
                ),
                using="bm25",
                query_filter=query_filter,
                limit=top_k,
                with_payload=True,
            )

            return [
                {
                    "id": str(point.id),
                    "score": point.score or 0.0,
                    "payload": point.payload or {},
                }
                for point in results.points
            ]
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []

    def _and_match_search(
        self,
        keywords: List[str],
        query_filter: models.Filter,
        top_k: int,
    ) -> List[Dict]:
        """Search for chunks matching claim keywords using AND logic with relaxation.

        Strategy:
        1. Try ALL keywords ANDed — finds exact phrase matches
        2. If too few results, progressively drop the least specific keyword
        3. Score by how many keywords matched (tighter match = higher score)

        This solves the dilution problem: for "Do not freeze VYVGART HYTRULO",
        searching for "freeze" alone matches 15 chunks across all drugs, but
        "freeze" AND "vyvgart" narrows it to exactly 4 VYVGART storage chunks.
        """
        # Filter out rewriter/noise terms that match everything
        NOISE = {
            "evidence", "supports", "support", "supporting", "claim",
            "avoiding", "recommendation", "approach", "method",
            "according", "regarding", "concerning", "suggests",
            "patients", "treated", "treatment", "study", "clinical",
        }
        specific_kws = [kw for kw in keywords if kw.lower() not in NOISE and len(kw) >= 3]
        if not specific_kws:
            specific_kws = keywords[:5]

        # Cap at 8 keywords to avoid over-constraining
        specific_kws = specific_kws[:8]

        all_results: Dict[str, Dict] = {}  # id -> {payload, match_count}

        # Progressive relaxation: try N keywords, then N-1, then N-2...
        # but minimum 1 keyword
        for n_required in range(len(specific_kws), 0, -1):
            # Try combinations of n_required keywords
            # For efficiency, only try dropping from the END (least specific usually)
            kw_subset = specific_kws[:n_required]

            text_conditions = [
                models.FieldCondition(
                    key="text",
                    match=models.MatchText(text=kw),
                )
                for kw in kw_subset
            ]

            # Add keyword inflections for better recall
            # e.g., freeze → frozen, freezing
            inflected_conditions = []
            for kw in kw_subset:
                variants = {kw}
                if kw.endswith("e"):
                    variants.add(kw + "d")   # freeze→freezed (may not help)
                    variants.add(kw[:-1] + "ing")  # freeze→freezing
                    variants.add(kw + "s")   # freeze→freezes
                    if kw == "freeze":
                        variants.add("frozen")
                elif kw.endswith("ing"):
                    variants.add(kw[:-3])    # warming→warm
                    variants.add(kw[:-3] + "ed")  # warming→warmed
                    variants.add(kw[:-3] + "e")   # warming→warme (harmless)
                # Use the original keyword (no inflection needed for MatchText as it's substring)
                pass

            combined_must = list(query_filter.must or []) + text_conditions
            combined_filter = models.Filter(
                must=combined_must,
                must_not=query_filter.must_not,
            )

            try:
                results = self._client.scroll(
                    collection_name=self._collection,
                    scroll_filter=combined_filter,
                    limit=top_k,
                    with_payload=True,
                )
                points = results[0]

                for point in points:
                    pid = str(point.id)
                    if pid not in all_results:
                        all_results[pid] = {
                            "id": pid,
                            "payload": point.payload or {},
                            "match_level": n_required,  # higher = tighter match
                        }

                # If we got enough results at this level, stop relaxing
                if len(points) >= 3:
                    logger.debug(f"AND-match: {len(points)} results with {n_required}/{len(specific_kws)} keywords")
                    break

            except Exception as e:
                logger.debug(f"AND-match with {n_required} keywords failed: {e}")
                continue

        # Score by match level (how many keywords matched simultaneously)
        scored = []
        for pid, data in all_results.items():
            scored.append({
                "id": pid,
                "score": data["match_level"] / max(len(specific_kws), 1),
                "payload": data["payload"],
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        logger.info(
            f"AND-match search: {len(scored)} results from "
            f"{len(specific_kws)} keywords: {specific_kws}"
        )
        return scored[:top_k]

    def _text_search(
        self,
        keywords: List[str],
        query_filter: models.Filter,
        top_k: int,
    ) -> List[Dict]:
        """Execute text keyword search on Qdrant full-text index.

        Searches each keyword individually via separate MatchText queries,
        then aggregates results by keyword overlap count. This avoids the
        issue of MatchText treating multi-word queries as phrase matches.
        """
        # --- Filter out rewriter noise ---
        # The GPT rewriter adds these to EVERY query; they match everything
        REWRITER_NOISE = {
            "evidence", "supports", "support", "supporting", "claim",
            "avoiding", "recommendation", "approach", "method",
            "according", "regarding", "concerning", "suggests",
        }

        # Common clinical words match too many chunks
        COMMON_CLINICAL = {
            "patients", "treated", "treatment", "study", "clinical",
            "adverse", "reactions", "occurred", "placebo", "compared",
            "versus", "results", "data", "safety", "efficacy",
            "dose", "mg", "administration", "recommended", "use",
            "risk", "events", "reported", "trials", "subjects",
        }

        ALL_NOISE = REWRITER_NOISE | COMMON_CLINICAL

        specific = [kw for kw in keywords if kw not in ALL_NOISE and len(kw) > 2]
        common = [kw for kw in keywords if kw in COMMON_CLINICAL and kw not in REWRITER_NOISE]
        # Take up to 12 specific terms first, then fill remaining with common
        search_keywords = (specific[:12] + common[:4])[:14]

        if not search_keywords:
            search_keywords = [kw for kw in keywords if kw not in REWRITER_NOISE][:6]

        # Collect points that match ANY keyword (OR logic)
        point_matches: Dict[str, Dict] = {}  # id -> {payload, keywords_matched}

        # Expand keywords with common inflection variants
        # Qdrant MatchText is exact substring — "frozen" won't match "freeze"
        expanded_keywords = set(search_keywords)
        for kw in search_keywords:
            # Add base form and common suffixes
            if kw.endswith("ed"):
                expanded_keywords.add(kw[:-2])  # frozen→ N/A, warmed→warm
                expanded_keywords.add(kw[:-1])   # used→us (handled by len filter)
                expanded_keywords.add(kw[:-2] + "e")  # stored→store
                expanded_keywords.add(kw[:-2] + "ing")  # warmed→warming
            elif kw.endswith("en"):
                expanded_keywords.add(kw[:-2])   # frozen→froz (not great)
                expanded_keywords.add(kw[:-2] + "e")  # frozen→froze
                expanded_keywords.add(kw[:-1] + "ing")  # frozen→frozening N/A
                # Special: frozen→freeze
                if kw == "frozen": expanded_keywords.add("freeze")
            elif kw.endswith("ing"):
                expanded_keywords.add(kw[:-3])   # warming→warm
                expanded_keywords.add(kw[:-3] + "e")  # storing→store
                expanded_keywords.add(kw[:-3] + "ed")  # warming→warmed
            elif kw.endswith("s") and not kw.endswith("ss"):
                expanded_keywords.add(kw[:-1])   # syringes→syringe
            elif kw.endswith("tion"):
                expanded_keywords.add(kw[:-4] + "t")  # injection→inject
                expanded_keywords.add(kw[:-4] + "ted")  # injection→injected
            # Also add with 'e' suffix for base words
            if len(kw) >= 4 and not kw.endswith("e"):
                expanded_keywords.add(kw + "e")  # freez→freeze (won't harm)
        # Filter too-short variants
        expanded_keywords = {k for k in expanded_keywords if len(k) >= 3}
        all_search_terms = list(expanded_keywords)
        logger.info(f"Keyword expansion: {len(search_keywords)} → {len(all_search_terms)} terms")

        for kw in all_search_terms:
            text_condition = models.FieldCondition(
                key="text",
                match=models.MatchText(text=kw),
            )

            combined_must = list(query_filter.must or []) + [text_condition]
            combined_filter = models.Filter(
                must=combined_must,
                must_not=query_filter.must_not,
            )

            try:
                results = self._client.scroll(
                    collection_name=self._collection,
                    scroll_filter=combined_filter,
                    limit=top_k,
                    with_payload=True,
                )
                points = results[0]

                for point in points:
                    pid = str(point.id)
                    if pid not in point_matches:
                        point_matches[pid] = {
                            "id": pid,
                            "payload": point.payload or {},
                            "matched_keywords": set(),
                        }
                    point_matches[pid]["matched_keywords"].add(kw)

            except Exception as e:
                logger.debug(f"Text search for keyword '{kw}' failed: {e}")
                continue

        # Score by keyword overlap count
        scored = []
        for pid, data in point_matches.items():
            match_count = len(data["matched_keywords"])
            scored.append({
                "id": pid,
                "score": match_count / max(len(search_keywords), 1),
                "payload": data["payload"],
            })

        # Sort by match count descending
        scored.sort(key=lambda x: x["score"], reverse=True)
        logger.info(f"Text search: {len(scored)} points across {len(search_keywords)} keywords")
        return scored[:top_k]

    def _rrf_fuse(
        self,
        dense_results: List[Dict],
        text_results: List[Dict],
    ) -> List[Dict]:
        """Fuse two ranked lists using RRF. Calls the 3-way method with empty exact."""
        return self._rrf_fuse_3(dense_results, text_results, [])

    def _rrf_fuse_3(
        self,
        dense_results: List[Dict],
        text_results: List[Dict],
        exact_results: List[Dict],
    ) -> List[Dict]:
        """Fuse three ranked lists using Reciprocal Rank Fusion.

        Weights are redistributed across 3 signals:
          - Dense (MedCPT): 50% — semantic understanding
          - BM25 sparse:    25% — proper lexical matching with stemming
          - Exact keywords:  25% — ensures verbatim claim phrases surface

        When exact_results is empty, dense gets 70% and text gets 30% (original).
        """
        has_exact = len(exact_results) > 0
        if has_exact:
            w_dense = 0.50
            w_text = 0.25
            w_exact = 0.25
        else:
            w_dense = self._dense_weight
            w_text = self._text_weight
            w_exact = 0.0

        # Build rank maps (1-indexed)
        dense_ranks = {r["id"]: i + 1 for i, r in enumerate(dense_results)}
        text_ranks = {r["id"]: i + 1 for i, r in enumerate(text_results)}
        exact_ranks = {r["id"]: i + 1 for i, r in enumerate(exact_results)}

        # Collect all unique document IDs
        all_ids = set(dense_ranks.keys()) | set(text_ranks.keys()) | set(exact_ranks.keys())

        # Collect payloads from whichever source has them
        payloads = {}
        for r in dense_results:
            payloads[r["id"]] = r["payload"]
        for r in text_results:
            if r["id"] not in payloads:
                payloads[r["id"]] = r["payload"]
        for r in exact_results:
            if r["id"] not in payloads:
                payloads[r["id"]] = r["payload"]

        # Also store raw scores for debugging
        dense_scores = {r["id"]: r["score"] for r in dense_results}
        text_scores = {r["id"]: r["score"] for r in text_results}
        exact_scores = {r["id"]: r["score"] for r in exact_results}

        # Compute RRF scores
        fused = []
        for doc_id in all_ids:
            rrf_score = 0.0

            if doc_id in dense_ranks:
                rrf_score += w_dense * (1.0 / (RRF_K + dense_ranks[doc_id]))
            if doc_id in text_ranks:
                rrf_score += w_text * (1.0 / (RRF_K + text_ranks[doc_id]))
            if doc_id in exact_ranks:
                rrf_score += w_exact * (1.0 / (RRF_K + exact_ranks[doc_id]))

            # ── Unpack doc_metadata into flat fields the UI expects ──────────
            payload = payloads.get(doc_id, {})
            dm = payload.get("doc_metadata") or {}
            if not isinstance(dm, dict):
                dm = {}

            dm_title   = dm.get("title", "")
            dm_authors = dm.get("authors_str") or ", ".join(dm.get("authors", [])) or ""
            dm_year    = dm.get("year", "")
            dm_journal = dm.get("journal", "")
            dm_doi     = dm.get("doi", "")
            # page_range = journal page range (e.g. "1092–1099"); use as display page
            dm_page    = dm.get("page_range") or dm.get("page") or payload.get("page")

            fused.append({
                "id": doc_id,
                "rrf_score": round(rrf_score, 6),
                "dense_score": round(dense_scores.get(doc_id, 0.0), 4),
                "text_score": round(text_scores.get(doc_id, 0.0), 4),
                "exact_score": round(exact_scores.get(doc_id, 0.0), 4),
                "dense_rank": dense_ranks.get(doc_id),
                "text_rank": text_ranks.get(doc_id),
                "exact_rank": exact_ranks.get(doc_id),
                "text": payload.get("text", ""),
                "ref_id": payload.get("ref_id", ""),
                # ref_title  → paper title from doc_metadata.title
                "ref_title":  dm_title or payload.get("ref_title", ""),
                # page       → journal page range (or raw page if present)
                "page":       dm_page,
                "rt_id": payload.get("rt_id", ""),
                "section": payload.get("section", ""),
                "segment_type": payload.get("segment_type", ""),
                "sent_id": payload.get("sent_id", ""),
                # Flat doc-level fields the UI reference card reads
                "doc_title":   dm_title,
                "doc_author":  dm_authors,
                "doc_year":    str(dm_year) if dm_year else "",
                "doc_journal": dm_journal,
                "doc_doi":     dm_doi,
                # Keep full nested object for any future use
                "doc_metadata": dm,
                "doc_references": payload.get("doc_references", []),
                "numeric_tokens": payload.get("numeric_tokens", []),
                "ref_category": payload.get("ref_category", ""),
                "reference_type_name": payload.get("reference_type_name", ""),
            })

        return fused

    def _cross_encoder_rerank(
        self,
        claim_text: str,
        candidates: List[Dict],
        top_k: int = 50,
    ) -> List[Dict]:
        """Re-rank candidates using a cross-encoder on (claim, passage) pairs.

        The cross-encoder sees both texts together, enabling it to match
        specific numbers, drug names, and AE terms that bi-encoder misses.

        Scoring: final = 0.4 * normalized_cross_encoder + 0.6 * normalized_rrf
        This ensures cross-encoder boosts relevant passages without
        completely overriding the retrieval signal.
        """
        import time

        t = time.time()

        # Lazily load cross-encoder
        if self._cross_encoder is None:
            try:
                from sentence_transformers import CrossEncoder

                cache_dir = os.getenv("HF_HOME", None)
                self._cross_encoder = CrossEncoder(
                    self._cross_encoder_model,
                    device="cpu",
                    cache_folder=cache_dir,
                )
                logger.info(f"Loaded cross-encoder: {self._cross_encoder_model}")
            except ImportError:
                logger.warning(
                    "sentence-transformers not installed — skipping cross-encoder re-ranking"
                )
                return candidates

        # Build (claim, passage) pairs for scoring
        pairs = []
        for c in candidates:
            passage_text = c.get("text", "")
            # Truncate very long passages to avoid exceeding model max length (512 tokens)
            if len(passage_text) > 1500:
                passage_text = passage_text[:1500]
            pairs.append([claim_text[:1000], passage_text])

        # Score all pairs in one batch
        try:
            scores = self._cross_encoder.predict(pairs, show_progress_bar=False)
        except Exception as e:
            logger.error(f"Cross-encoder scoring failed: {e}")
            return candidates

        # Normalize cross-encoder scores to [0, 1]
        min_score = float(min(scores))
        max_score = float(max(scores))
        score_range = max_score - min_score if max_score > min_score else 1.0

        # Normalize RRF scores to [0, 1]
        rrf_scores = [c["rrf_score"] for c in candidates]
        min_rrf = min(rrf_scores)
        max_rrf = max(rrf_scores)
        rrf_range = max_rrf - min_rrf if max_rrf > min_rrf else 1.0

        # Combine: weighted blend of cross-encoder + RRF
        CE_WEIGHT = 0.4
        RRF_WEIGHT = 0.6

        for i, c in enumerate(candidates):
            ce_norm = (float(scores[i]) - min_score) / score_range
            rrf_norm = (c["rrf_score"] - min_rrf) / rrf_range
            c["cross_encoder_score"] = round(float(scores[i]), 4)
            c["cross_encoder_norm"] = round(ce_norm, 4)
            c["rerank_score"] = round(CE_WEIGHT * ce_norm + RRF_WEIGHT * rrf_norm, 6)

        # Sort by combined re-rank score
        candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

        elapsed = round(time.time() - t, 2)
        logger.info(
            f"Cross-encoder re-rank: {len(candidates)} candidates in {elapsed}s "
            f"(CE range: {min_score:.2f}..{max_score:.2f})"
        )

        # Replace rrf_score with rerank_score for downstream compatibility
        for c in candidates:
            c["rrf_score"] = c["rerank_score"]

        return candidates[:top_k]

    def _apply_tier_boost(
        self,
        results: List[Dict],
        primary: Set[str],
        acceptable: Set[str],
        conditional: Set[str],
    ) -> List[Dict]:
        """Apply tier-based score multipliers to RRF-fused results."""
        for r in results:
            rt_id = r.get("rt_id", "")

            if rt_id in primary:
                boost = self._boosts[EvidenceTier.PRIMARY]
                tier = "P"
            elif rt_id in acceptable:
                boost = self._boosts[EvidenceTier.ACCEPTABLE]
                tier = "A"
            elif rt_id in conditional:
                boost = self._boosts[EvidenceTier.CONDITIONAL]
                tier = "C"
            else:
                boost = 0.5
                tier = "?"

            r["tier"] = tier
            r["tier_boost"] = boost
            r["final_score"] = round(r["rrf_score"] * (1.0 + boost), 6)

        return results

    def _apply_diversity_cap(
        self,
        results: List[Dict],
        max_per_ref_id: int = 5,
    ) -> List[Dict]:
        """Cap the number of chunks from any single ref_id.

        Requirements §1.2: 'Each reference should contribute unique,
        non-duplicative support. Redundant references that contribute no
        distinct element should be removed.'

        After tier boosting, one high-authority document (e.g. the PI) can
        dominate the top N slots with near-identical chunks. This cap ensures
        diverse sources reach the judge while preserving depth within each source.

        Args:
            results: RRF-fused + tier-boosted results (unsorted or sorted).
            max_per_ref_id: Maximum chunks to retain per unique ref_id.

        Returns:
            Filtered list with at most max_per_ref_id chunks per source.
        """
        counts: Dict[str, int] = {}
        capped = []
        for r in results:
            ref_id = r.get("ref_id", "__unknown__")
            counts[ref_id] = counts.get(ref_id, 0)
            if counts[ref_id] < max_per_ref_id:
                capped.append(r)
                counts[ref_id] += 1
        if len(capped) < len(results):
            logger.info(
                f"Diversity cap: {len(results)} → {len(capped)} results "
                f"(max {max_per_ref_id}/ref_id)"
            )
        return capped

    def _detect_brand_names(self, claim_text: str, results: List[Dict]) -> set:
        """Auto-detect product/brand-name tokens in a claim.

        Returns a set of lowercase brand-name strings that are likely product
        names. Uses two signals:

        Signal 1 — ref_id match (primary):
            If a capitalized token from the claim appears in a result's ref_id,
            it's almost certainly a product name (documents are named after drugs).

        Signal 2 — chunk text frequency (fallback for vague ref_ids):
            If the ref_id is generic (e.g. 'doc_001'), check how many result
            chunks mention the candidate in their text. If 3+ chunks mention it,
            it's likely a product name that the corpus tracks by name.
            Threshold of 3 avoids false positives from incidental mentions.

        Fully automatic — no hardcoded product list needed.
        """
        COMMON = {
            "do", "not", "the", "and", "for", "use", "with", "into",
            "that", "this", "from", "have", "been", "should", "store",
            "patients", "always", "prior", "after", "before",
            "injection", "prefilled", "syringe", "temperature",
            "room", "days", "make", "sure", "check", "discard",
            "adhere", "stage",  # clinical trial terms, not brand names
        }
        tokens = re.findall(r"\b[A-Z][A-Za-z]{1,}\b", claim_text)
        candidates = {t.lower() for t in tokens if t.lower() not in COMMON and len(t) >= 3}
        if not candidates or not results:
            return set()

        # Signal 1: ref_id match
        ref_id_blob = " ".join(r.get("ref_id", "").lower() for r in results)
        found_via_ref = {c for c in candidates if c in ref_id_blob}

        # Signal 2: chunk text frequency (fallback for vague ref_ids)
        found_via_text = set()
        for c in candidates - found_via_ref:
            count = sum(1 for r in results if c in r.get("text", "").lower())
            if count >= 3:
                found_via_text.add(c)

        detected = found_via_ref | found_via_text
        if found_via_text:
            logger.debug(
                f"Brand detection via chunk text (vague ref_ids): {found_via_text}"
            )
        return detected


    def _apply_product_boost(
        self,
        results: List[Dict],
        claim_text: str,
        boost_factor: float = 1.5,
    ) -> List[Dict]:
        """Boost results from documents matching the product named in the claim.

        When a claim says "Do not freeze VYVGART HYTRULO", we want the
        VYVGART PI to rank above the Hizentra PI even if both contain
        similar storage instructions. This applies a multiplicative boost
        to results whose ref_id contains the product name.

        Product names are detected dynamically via _detect_brand_names().
        """
        # Extract potential product names: uppercase words or Title-case
        # words that aren't common English (e.g., VYVGART, Hizentra, Gamunex)
        COMMON_WORDS = {
            "do", "not", "the", "and", "for", "use", "with", "into",
            "that", "this", "from", "have", "been", "should", "store",
            "patients", "always", "prior", "after", "before",
            "injection", "prefilled", "syringe", "temperature",
            "room", "days", "make", "sure", "check", "discard",
        }
        tokens = re.findall(r'\b[A-Z][A-Za-z]{1,}\b', claim_text)
        # Keep tokens that aren't common words (likely product/brand names)
        candidate_names = [
            t.lower() for t in tokens
            if t.lower() not in COMMON_WORDS and len(t) >= 3
        ]

        if not candidate_names:
            return results

        # Check which candidate names actually appear in any ref_id
        # (confirms they're product/document names, not random words)
        all_ref_ids = {r.get("ref_id", "").lower() for r in results}
        ref_id_blob = " ".join(all_ref_ids)

        matched_products = [
            name for name in candidate_names
            if name in ref_id_blob
        ]

        if not matched_products:
            return results

        boosted_count = 0
        for r in results:
            ref_id_lower = r.get("ref_id", "").lower()

            is_product_match = any(
                p in ref_id_lower for p in matched_products
            )

            if is_product_match:
                r["final_score"] = round(r["final_score"] * boost_factor, 6)
                r["product_boost"] = True
                boosted_count += 1
            else:
                r["product_boost"] = False

        if boosted_count:
            logger.info(
                f"Product boost: {boosted_count}/{len(results)} results "
                f"boosted for products: {matched_products}"
            )

        return results
