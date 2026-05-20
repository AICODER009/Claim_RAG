"""End-to-End Substantiation Test Runner.

Reads real claims from the xlsx file, runs them through the full pipeline:
  1. Classify (or use pre-assigned CT-ID from xlsx)
  2. Rewrite claim -> question
  3. Encode via MedCPT Query Encoder
  4. Hybrid retrieve from Qdrant (dense + text, RRF fusion)
  5. Judge via Claude
  6. Logic gate -> verdict

Uses Anthropic (Claude) for all LLM calls since OpenAI quota may be exhausted.

Usage:
    $env:PYTHONIOENCODING="utf-8"
    C:\\Users\\Baku\\miniconda3\\python.exe new_pipeline/scripts/run_e2e_test.py
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

# Force HF cache to D drive BEFORE any HuggingFace imports
os.environ["HF_HOME"] = r"D:\hf_cache"
os.environ["TRANSFORMERS_CACHE"] = r"D:\hf_cache"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import openpyxl
import torch
import numpy as np
from qdrant_client import QdrantClient
from transformers import AutoModel, AutoTokenizer

from new_pipeline.retrieval.claim_rewriter import ClaimRewriter
from new_pipeline.retrieval.mapping_matrix import MappingMatrix
from new_pipeline.retrieval.hybrid_retriever import HybridRetriever
from new_pipeline.evaluation.substantiation_judge import SubstantiationJudge
from new_pipeline.evaluation.logic_gate import LogicGate
from new_pipeline.schemas import (
    ClaimClassification,
    CoverageResult,
    CoverageVerdict,
    PICOTComponents,
    SubAssertionResult,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CLAIMS_XLSX = Path(__file__).parent.parent / "claims" / "ALL_CLAIMS_COMBINED_categorized_v5.xlsx"
RESULTS_DIR = Path(__file__).parent.parent / "tests"
CATEGORIZATION_DIR = Path(os.getenv(
    "CATEGORIZATION_DIR",
    "D:/revisto_evidence_aligned_clean/categorization",
))

# How many claims to test (pick diverse CT-IDs)
MAX_CLAIMS = 10

# CT-IDs to sample from (one claim per CT-ID for diversity)
TARGET_CT_IDS = [
    "CT-201",  # Efficacy — primary endpoint
    "CT-301",  # Safety / tolerability
    "CT-101",  # Indication (on-label)
    "CT-501",  # Comparative
    "CT-307",  # Drug interaction / contraindication
    "CT-603",  # Dosing / administration
    "CT-311",  # Mechanism of action
    "CT-605",  # Storage / handling
    "CT-108",  # Disease state
    "CT-601",  # Formulation / device
]


# ---------------------------------------------------------------------------
# Load claims from xlsx
# ---------------------------------------------------------------------------

def load_test_claims() -> List[Dict]:
    """Load diverse claims from the xlsx file.

    Picks one claim per CT-ID from TARGET_CT_IDS.
    Prefers 'Original' category, skips 'Non-claim'.
    Uses pre-assigned CT-IDs from Col 12 as ground truth.
    """
    logger.info(f"Loading claims from: {CLAIMS_XLSX}")
    wb = openpyxl.load_workbook(str(CLAIMS_XLSX), read_only=True)
    ws = wb["All Claims Combined"]

    # Group claims by CT-ID
    by_ct_id: Dict[str, List[Dict]] = {}
    for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        claim_text = row[4] or ""
        category = row[10] or ""
        ct_id = row[12] or ""

        if not claim_text or not ct_id or category == "Non-claim":
            continue
        if len(claim_text.strip()) < 20:
            continue

        if ct_id not in by_ct_id:
            by_ct_id[ct_id] = []
        by_ct_id[ct_id].append({
            "row": row_num,
            "claim": claim_text.strip(),
            "ground_truth_ct_id": ct_id,
            "category": category,
            "source_type": str(row[2] or "").strip().lower(),
            "document": row[0] or "",
            "references": row[6] or "",
        })

    wb.close()

    # Pick one claim per target CT-ID
    # Prefer: text source > figure source (figures can have OCR errors),
    # then longest within text claims
    selected = []
    for ct_id in TARGET_CT_IDS:
        if ct_id in by_ct_id:
            candidates = by_ct_id[ct_id]
            # Prefer text source type over figure (figures may have OCR errors)
            text_candidates = [c for c in candidates if c["source_type"] == "text"]
            pool = text_candidates if text_candidates else candidates
            best = max(pool, key=lambda c: len(c["claim"]))
            selected.append(best)
            logger.info(f"  {ct_id}: selected row {best['row']} ({len(best['claim'])} chars)")
        else:
            logger.warning(f"  {ct_id}: no claims found in xlsx")

    logger.info(f"Selected {len(selected)} claims across {len(set(c['ground_truth_ct_id'] for c in selected))} CT-IDs")
    return selected[:MAX_CLAIMS]


# ---------------------------------------------------------------------------
# Pipeline components (manual init to avoid full SubstantiationPipeline)
# ---------------------------------------------------------------------------

def init_components():
    """Initialize all pipeline components using Anthropic."""
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not anthropic_key:
        logger.error("ANTHROPIC_API_KEY not set")
        sys.exit(1)

    judge_model = os.getenv("JUDGE_MODEL", "claude-sonnet-4-20250514")
    hf_token = os.getenv("HF_TOKEN", "")

    components = {}

    # Claim Rewriter (Anthropic)
    logger.info("Init: ClaimRewriter (Anthropic)...")
    components["rewriter"] = ClaimRewriter(
        provider="anthropic",
        model=judge_model,
        api_key=anthropic_key,
    )

    # Mapping Matrix
    mapping_path = CATEGORIZATION_DIR / "Claim-to-Reference_Mapping.md"
    logger.info(f"Init: MappingMatrix from {mapping_path.name}...")
    components["matrix"] = MappingMatrix(mapping_path=mapping_path)

    # MedCPT Query Encoder
    query_model_name = os.getenv("QUERY_EMBED_MODEL", "ncbi/MedCPT-Query-Encoder")
    logger.info(f"Init: MedCPT Query Encoder ({query_model_name})...")

    hf_cache = r"D:\hf_cache"
    components["query_tokenizer"] = AutoTokenizer.from_pretrained(
        query_model_name,
        token=hf_token if hf_token else None,
        cache_dir=hf_cache,
    )
    components["query_model"] = AutoModel.from_pretrained(
        query_model_name,
        token=hf_token if hf_token else None,
        cache_dir=hf_cache,
    ).eval()

    # Qdrant Hybrid Retriever
    logger.info("Init: HybridRetriever (Qdrant)...")
    qdrant_client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
        timeout=60,
    )
    collection = os.getenv("QDRANT_COLLECTION", "verifai_mlr")

    components["retriever"] = HybridRetriever(
        qdrant_client=qdrant_client,
        collection_name=collection,
        mapping_matrix=components["matrix"],
        tier_p_boost=2.0,
        tier_a_boost=1.0,
        tier_c_boost=0.5,
        dense_weight=0.7,
        text_weight=0.3,
    )

    # Substantiation Judge (Claude)
    reqs_path = CATEGORIZATION_DIR / "Claim_Substantiation_Requirements_v1_1.md"
    logger.info("Init: SubstantiationJudge (Claude)...")
    components["judge"] = SubstantiationJudge(
        api_key=anthropic_key,
        model=judge_model,
        requirements_path=reqs_path,
    )

    # Logic Gate
    components["logic_gate"] = LogicGate(
        pass_threshold=80.0,
        soft_flag_threshold=60.0,
        enforce_fair_balance=True,
        rounding_tolerance_pct=2.0,
    )

    logger.info("All components initialized.")
    return components


@torch.no_grad()
def encode_query(question: str, tokenizer, model) -> List[float]:
    """Encode a question using MedCPT Query Encoder."""
    encoded = tokenizer(
        question, max_length=256, padding=True,
        truncation=True, return_tensors="pt",
    )
    output = model(**encoded)
    embedding = output.last_hidden_state[:, 0, :]
    return embedding.cpu().numpy().flatten().tolist()


# ---------------------------------------------------------------------------
# Process a single claim
# ---------------------------------------------------------------------------

def process_claim(claim_data: Dict, components: Dict) -> Dict:
    """Run a single claim through the full pipeline."""
    claim_text = claim_data["claim"]
    gt_ct_id = claim_data["ground_truth_ct_id"]

    result = {
        "claim_text": claim_text,
        "ground_truth_ct_id": gt_ct_id,
        "category": claim_data["category"],
        "document": claim_data["document"],
        "xlsx_row": claim_data["row"],
    }
    timings = {}

    # --- Step 1: Use ground truth CT-ID (skip classifier to save cost) ---
    # Build minimal classification and PICOT from ground truth
    classification = ClaimClassification(
        ct_id=gt_ct_id,
        claim_type_name=gt_ct_id,  # Will be filled by matrix if available
        confidence=1.0,
    )
    picot = PICOTComponents()  # Empty PICOT — judge will note "Not specified"
    result["classification"] = {"ct_id": gt_ct_id, "source": "xlsx_ground_truth"}

    # --- Step 2: Rewrite claim -> question ---
    t = time.time()
    try:
        question = components["rewriter"].rewrite(claim_text)
    except Exception as e:
        logger.error(f"Rewriter failed: {e}")
        question = claim_text  # Fallback
    timings["rewrite"] = round(time.time() - t, 2)
    result["rewritten_query"] = question
    logger.info(f"  [Step 2] Rewrite: {question[:80]}...")

    # --- Step 3: Encode query ---
    t = time.time()
    query_vector = encode_query(
        question,
        components["query_tokenizer"],
        components["query_model"],
    )
    timings["encode"] = round(time.time() - t, 3)
    logger.info(f"  [Step 3] Encoded: {len(query_vector)}-dim vector")

    # --- Step 4: Hybrid retrieve ---
    # Exclude competitor drug documents to prevent cross-product retrieval
    COMPETITOR_REF_IDS = {
        "hizentra-prescribing-information",
        "Package-Insert----Gamunex-C",
        "Solu-Medrol PI Dec 2021",
        "HYQVIA_USA_ENG",
    }
    t = time.time()
    try:
        candidates = components["retriever"].search(
            query_vector=query_vector,
            query_text=question,
            original_claim_text=claim_text,
            ct_id=gt_ct_id,
            exclude_ref_ids=COMPETITOR_REF_IDS,
            final_top_k=50,
        )
    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        candidates = []
    timings["retrieve"] = round(time.time() - t, 2)
    logger.info(f"  [Step 4] Retrieved: {len(candidates)} candidates")

    # Top 20 for judge — ensures AE tables and multi-section claims get covered
    judge_passages = candidates[:20]
    result["retrieval"] = {
        "total_candidates": len(candidates),
        "judge_passages_count": len(judge_passages),
        "passages": [
            {
                "ref_id": p.get("ref_id", ""),
                "rt_id": p.get("rt_id", ""),
                "tier": p.get("tier", "?"),
                "reference_type_name": p.get("reference_type_name", ""),
                "dense_score": p.get("dense_score", 0),
                "text_score": p.get("text_score", 0),
                "rrf_score": p.get("rrf_score", 0),
                "final_score": p.get("final_score", 0),
                "text_preview": p.get("text", "")[:200],
            }
            for p in judge_passages
        ],
    }

    # --- Step 5: Judge evaluation ---
    if not judge_passages:
        logger.warning("  [Step 5] No passages -- skipping judge")
        judge_raw = {
            "sub_assertions": [],
            "coverage_score": 0.0,
            "overall_assessment": "No evidence passages retrieved.",
        }
        timings["judge"] = 0
    else:
        t = time.time()
        try:
            judge_raw = components["judge"].evaluate(
                claim_text=claim_text,
                classification=classification,
                picot=picot,
                evidence_passages=judge_passages,
            )
        except Exception as e:
            logger.error(f"Judge failed: {e}")
            judge_raw = {
                "sub_assertions": [],
                "coverage_score": 0.0,
                "overall_assessment": f"Judge error: {str(e)}",
            }
        timings["judge"] = round(time.time() - t, 2)

    coverage_score = judge_raw.get("coverage_score", 0.0)
    logger.info(f"  [Step 5] Judge: coverage={coverage_score}")
    result["judge"] = judge_raw

    # --- Step 6: Logic gate ---
    if judge_passages and coverage_score > 0:
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
            coverage_score=coverage_score,
            picot=picot,
            picot_alignment=judge_raw.get("picot_alignment", {}),
        )
        t = time.time()
        verdict = components["logic_gate"].evaluate(
            coverage_result=coverage_result,
            judge_raw=judge_raw,
            claim_ct_id=gt_ct_id,
        )
        timings["logic_gate"] = round(time.time() - t, 4)
    else:
        verdict = {
            "verdict": CoverageVerdict.BLOCK.value,
            "coverage_score": 0.0,
            "flags": ["No evidence retrieved"],
            "blockers": ["No evidence passages found"],
        }
        timings["logic_gate"] = 0

    result["verdict"] = verdict
    result["timings"] = timings
    result["total_time"] = round(sum(timings.values()), 2)

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n" + "=" * 80)
    print("E2E SUBSTANTIATION TEST RUNNER")
    print("=" * 80)

    # Load claims
    claims = load_test_claims()
    if not claims:
        logger.error("No claims loaded!")
        return

    # Init components
    components = init_components()

    # Process each claim
    all_results = []
    for i, claim_data in enumerate(claims, 1):
        ct_id = claim_data["ground_truth_ct_id"]
        print(f"\n{'='*80}")
        print(f"CLAIM {i}/{len(claims)} [{ct_id}]")
        print(f"  {claim_data['claim'][:100]}...")
        print(f"{'='*80}")

        result = process_claim(claim_data, components)
        all_results.append(result)

        # Print summary
        v = result["verdict"]
        verdict_str = v.get("verdict", "?")
        score = v.get("coverage_score", 0)
        flags = len(v.get("flags", []))
        blockers = len(v.get("blockers", []))
        passages = result["retrieval"]["judge_passages_count"]
        total_t = result["total_time"]

        emoji = {"pass": "PASS", "soft_flag": "FLAG", "block": "BLOCK"}.get(verdict_str, "????")
        print(f"\n  VERDICT: {emoji} | coverage={score:.0f}% | "
              f"passages={passages} | flags={flags} | blockers={blockers} | "
              f"time={total_t}s")

        # Show top 3 retrieved passages
        for j, p in enumerate(result["retrieval"]["passages"][:3], 1):
            print(f"  Passage {j}: {p['ref_id'][:40]} | {p['rt_id']} | "
                  f"Tier {p['tier']} | rrf={p['rrf_score']:.4f}")

    # Save results
    RESULTS_DIR.mkdir(exist_ok=True)
    output_path = RESULTS_DIR / "e2e_substantiation_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nResults saved to: {output_path}")

    # Summary table
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"{'CT-ID':<10} {'Verdict':<10} {'Coverage':>8} {'Passages':>8} {'Time':>6}")
    print("-" * 50)
    for r in all_results:
        ct = r["ground_truth_ct_id"]
        v = r["verdict"].get("verdict", "?")
        s = r["verdict"].get("coverage_score", 0)
        p = r["retrieval"]["judge_passages_count"]
        t = r["total_time"]
        print(f"{ct:<10} {v:<10} {s:>7.0f}% {p:>8} {t:>5.1f}s")


if __name__ == "__main__":
    main()
