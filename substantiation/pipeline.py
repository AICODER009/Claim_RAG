"""Substantiation Pipeline — end-to-end claim matching orchestrator.

Chains all steps together:
  Step 1: ClaimClassifier.classify(claim) → CT-ID + PICOT
  Step 2: MappingMatrix.get_tiers(CT-ID) → P/A/C/N sets  [pre-retrieval]
  Step 3: ClaimRewriter.rewrite(claim) → question-form query
  Step 4: MedCPT QueryEncoder.encode(question) → 768-dim vector
  Step 5: HybridRetriever.search(vector, text, CT-ID) → RRF-fused passages
  Step 6: SubstantiationJudge.evaluate(claim, PICOT, passages) → coverage
  Step 7: LogicGate.evaluate(coverage, raw_judge, CT-ID) → verdict
  Step 8: AuditTrail.record(all_data) → JSON log
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import torch
from qdrant_client import QdrantClient
from transformers import AutoModel, AutoTokenizer

from ..classification.claim_classifier import ClaimClassifier
from ..config import PipelineConfig, load_config
from ..evaluation.logic_gate import LogicGate
from ..evaluation.substantiation_judge import SubstantiationJudge
from ..retrieval.claim_rewriter import ClaimRewriter
from ..retrieval.hybrid_retriever import HybridRetriever
from ..retrieval.mapping_matrix import MappingMatrix
from ..schemas import AuditRecord, CoverageVerdict

logger = logging.getLogger(__name__)


class SubstantiationPipeline:
    """End-to-end claim substantiation pipeline."""

    def __init__(self, config: Optional[PipelineConfig] = None):
        self._config = config or load_config()
        self._initialized = False

        # Lazy-init placeholders
        self._classifier: Optional[ClaimClassifier] = None
        self._rewriter: Optional[ClaimRewriter] = None
        self._matrix: Optional[MappingMatrix] = None
        self._retriever: Optional[HybridRetriever] = None
        self._judge: Optional[SubstantiationJudge] = None
        self._logic_gate: Optional[LogicGate] = None

        # MedCPT Query Encoder (loaded separately — lightweight)
        self._query_tokenizer = None
        self._query_model = None

    def initialize(self) -> None:
        """Initialize all pipeline components.

        Call this once before processing claims. Separated from __init__
        so you can configure before paying the load cost.
        """
        cfg = self._config
        t0 = time.time()

        # Step 1: Claim Classifier
        logger.info("Initializing ClaimClassifier...")
        self._classifier = ClaimClassifier(
            provider=cfg.llm.classifier_provider,
            model=cfg.llm.classifier_model,
            api_key=cfg.llm.openai_api_key,
            taxonomy_path=cfg.claim_classification_path,
        )

        # Step 2: Mapping Matrix (deterministic, no LLM)
        logger.info("Loading CT→RT mapping matrix...")
        self._matrix = MappingMatrix(
            mapping_path=cfg.claim_mapping_path,
        )

        # Step 3: Claim Rewriter
        logger.info("Initializing ClaimRewriter...")
        self._rewriter = ClaimRewriter(
            provider=cfg.llm.classifier_provider,
            model=cfg.llm.classifier_model,
            api_key=cfg.llm.openai_api_key,
        )

        # Step 4: MedCPT Query Encoder (load only the query side)
        logger.info(f"Loading MedCPT Query Encoder: {cfg.embedding.query_model}")
        self._query_tokenizer = AutoTokenizer.from_pretrained(
            cfg.embedding.query_model, token=cfg.embedding.hf_token,
        )
        self._query_model = AutoModel.from_pretrained(
            cfg.embedding.query_model, token=cfg.embedding.hf_token,
        ).eval()

        # Step 5: Hybrid Retriever (dense MedCPT + text keyword, RRF fusion)
        logger.info(f"Connecting to Qdrant: {cfg.qdrant.url[:50]}...")
        qdrant_client = QdrantClient(
            url=cfg.qdrant.url,
            api_key=cfg.qdrant.api_key,
            timeout=60,
        )
        self._retriever = HybridRetriever(
            qdrant_client=qdrant_client,
            collection_name=cfg.qdrant.collection_name,
            mapping_matrix=self._matrix,
            tier_p_boost=cfg.retrieval.tier_p_boost,
            tier_a_boost=cfg.retrieval.tier_a_boost,
            tier_c_boost=cfg.retrieval.tier_c_boost,
            dense_weight=cfg.retrieval.semantic_weight,
            text_weight=cfg.retrieval.lexical_weight,
        )

        # Step 6: Substantiation Judge (Claude)
        logger.info("Initializing SubstantiationJudge...")
        self._judge = SubstantiationJudge(
            api_key=cfg.llm.anthropic_api_key,
            model=cfg.llm.judge_model,
            requirements_path=cfg.substantiation_requirements_path,
        )

        # Step 7: Logic Gate (deterministic)
        self._logic_gate = LogicGate(
            pass_threshold=cfg.evaluation.pass_threshold,
            soft_flag_threshold=cfg.evaluation.soft_flag_threshold,
            enforce_fair_balance=cfg.evaluation.enforce_fair_balance,
            rounding_tolerance_pct=cfg.evaluation.rounding_tolerance_pct,
        )

        self._initialized = True
        logger.info(f"Pipeline initialized in {time.time() - t0:.1f}s")

    @torch.no_grad()
    def _encode_query(self, question: str) -> List[float]:
        """Encode a question-form query using MedCPT Query Encoder."""
        encoded = self._query_tokenizer(
            question,
            max_length=256,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        output = self._query_model(**encoded)
        embedding = output.last_hidden_state[:, 0, :]
        return embedding.cpu().numpy().flatten().tolist()

    def process_claim(
        self,
        claim_text: str,
        top_k: int = 50,
        judge_top_k: int = 5,
    ) -> Dict:
        """Process a single claim through the full pipeline.

        Args:
            claim_text: The pharmaceutical marketing claim.
            top_k: Number of candidates to retrieve from Qdrant.
            judge_top_k: Number of passages to send to the LLM judge.

        Returns:
            Dict with all pipeline outputs: classification, retrieval,
            judge evaluation, verdict, and timing.
        """
        if not self._initialized:
            raise RuntimeError("Pipeline not initialized. Call initialize() first.")

        timings = {}
        result = {"claim_text": claim_text}

        # ----- Step 1: Classify -----
        t = time.time()
        classification, picot = self._classifier.classify(claim_text)
        timings["classify"] = round(time.time() - t, 2)
        result["classification"] = {
            "ct_id": classification.ct_id,
            "claim_type_name": classification.claim_type_name,
            "secondary_ct_id": classification.secondary_ct_id,
            "confidence": classification.confidence,
        }
        result["picot"] = {
            "population": picot.population,
            "intervention": picot.intervention,
            "comparator": picot.comparator,
            "outcome": picot.outcome,
            "timeframe": picot.timeframe,
        }
        logger.info(f"[Step 1] Classified as {classification.ct_id} "
                     f"({classification.claim_type_name})")

        # ----- Step 2: Mapping Matrix -----
        t = time.time()
        tier_mappings = self._matrix.get_tiers(classification.ct_id)
        primary_rts = self._matrix.get_primary_rt_ids(classification.ct_id)
        allowed_rts = self._matrix.get_allowed_rt_ids(classification.ct_id)
        blocked_rts = self._matrix.get_blocked_rt_ids(classification.ct_id)
        timings["mapping"] = round(time.time() - t, 4)
        result["tier_info"] = {
            "total_mappings": len(tier_mappings),
            "primary_rt_ids": sorted(primary_rts),
            "blocked_rt_ids": sorted(blocked_rts),
        }
        logger.info(f"[Step 2] Mapping: {len(tier_mappings)} RT-IDs, "
                     f"P={len(primary_rts)}, N={len(blocked_rts)}")

        # ----- Step 3: Rewrite claim → question -----
        t = time.time()
        question = self._rewriter.rewrite(claim_text)
        timings["rewrite"] = round(time.time() - t, 2)
        result["rewritten_query"] = question
        logger.info(f"[Step 3] Rewrite: '{question}'")

        # ----- Step 4: Encode query -----
        t = time.time()
        query_vector = self._encode_query(question)
        timings["encode"] = round(time.time() - t, 3)
        logger.info(f"[Step 4] Encoded query: {len(query_vector)}-dim vector")

        # ----- Step 5: Hybrid Retrieve (dense + text, RRF fusion) -----
        t = time.time()
        candidates = self._retriever.search(
            query_vector=query_vector,
            query_text=question,
            ct_id=classification.ct_id,
            final_top_k=top_k,
        )
        timings["retrieve"] = round(time.time() - t, 2)
        logger.info(f"[Step 5] Retrieved {len(candidates)} candidates (RRF hybrid)")

        # Take top-K for judge
        judge_passages = candidates[:judge_top_k]
        result["retrieval"] = {
            "total_candidates": len(candidates),
            "judge_passages_count": len(judge_passages),
            "top_5_refs": [
                {
                    "ref_id": p["ref_id"],
                    "rt_id": p["rt_id"],
                    "tier": p["tier"],
                    "dense_score": p.get("dense_score", 0),
                    "text_score": p.get("text_score", 0),
                    "rrf_score": p.get("rrf_score", 0),
                    "final_score": p.get("final_score", 0),
                    "text_preview": p["text"][:150] + "...",
                }
                for p in judge_passages
            ],
        }

        # ----- Step 6: Judge evaluation -----
        if not judge_passages:
            logger.warning("[Step 6] No passages retrieved — skipping judge")
            judge_raw = {
                "sub_assertions": [],
                "coverage_score": 0.0,
                "picot_alignment": {},
                "secondary_citation_detected": False,
                "statistical_context_present": False,
                "overall_assessment": "No evidence passages retrieved.",
            }
            timings["judge"] = 0
        else:
            t = time.time()
            judge_raw = self._judge.evaluate(
                claim_text=claim_text,
                classification=classification,
                picot=picot,
                evidence_passages=judge_passages,
            )
            timings["judge"] = round(time.time() - t, 2)

        # Build CoverageResult from the raw judge output (no second LLM call)
        if judge_passages and judge_raw.get("coverage_score", 0) > 0:
            from ..schemas import CoverageResult, SubAssertionResult
            sub_assertions = [
                SubAssertionResult(
                    sub_assertion=sa.get("sub_assertion", ""),
                    is_covered=sa.get("is_covered", False),
                    verbatim_anchor=sa.get("evidence_text"),
                )
                for sa in judge_raw.get("sub_assertions", [])
            ]
            coverage_result = CoverageResult(
                claim_text=claim_text,
                sub_assertions=sub_assertions,
                coverage_score=judge_raw.get("coverage_score", 0.0),
                picot=picot,
                picot_alignment=judge_raw.get("picot_alignment", {}),
            )
        else:
            coverage_result = None

        result["judge"] = judge_raw
        logger.info(f"[Step 6] Judge: coverage={judge_raw.get('coverage_score', '?')}")

        # ----- Step 7: Logic Gate -----
        if coverage_result:
            t = time.time()
            verdict = self._logic_gate.evaluate(
                coverage_result=coverage_result,
                judge_raw=judge_raw,
                claim_ct_id=classification.ct_id,
            )
            timings["logic_gate"] = round(time.time() - t, 4)
        else:
            verdict = {
                "verdict": CoverageVerdict.BLOCK.value,
                "coverage_score": 0.0,
                "flags": ["No evidence retrieved"],
                "blockers": ["No evidence passages found in Qdrant"],
                "overall_assessment": "No evidence retrieved.",
            }
            timings["logic_gate"] = 0

        result["verdict"] = verdict
        result["timings"] = timings
        result["total_time"] = round(sum(timings.values()), 2)

        logger.info(
            f"[Step 7] VERDICT: {verdict['verdict']} "
            f"(coverage={verdict.get('coverage_score', 0):.0f}%, "
            f"flags={len(verdict.get('flags', []))}, "
            f"blockers={len(verdict.get('blockers', []))})"
        )

        return result
