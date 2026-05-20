#!/usr/bin/env python3
"""Full batch substantiation — processes ALL 2,075 claims.

Reads claims from xlsx, merges CT-IDs from both:
  1. Pre-classified (xlsx col 12)
  2. Newly classified (classified_missing_claims.json)

Runs the full substantiation pipeline on each claim and generates:
  - Per-claim audit JSON records
  - Portfolio-level coverage summary report

Features:
  - Resume capability: skips already-processed claims
  - Configurable concurrency (sequential by default)
  - Per-document portfolio grouping (Section 3.4)
  - Progress tracking with ETA
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

import openpyxl

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from new_pipeline.config import load_config
from new_pipeline.schemas import CoverageVerdict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CLAIMS_XLSX = Path(__file__).parent.parent / "claims" / "ALL_CLAIMS_COMBINED_categorized_v5.xlsx"
CLASSIFIED_JSON = Path(__file__).parent.parent / "claims" / "classified_missing_claims.json"
RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_FILE = RESULTS_DIR / "batch_substantiation_results.json"
REPORT_FILE = RESULTS_DIR / "portfolio_coverage_report.md"

# How many passages to retrieve per claim
TOP_K = 20


# ---------------------------------------------------------------------------
# Load claims
# ---------------------------------------------------------------------------

def load_all_claims() -> List[Dict]:
    """Load all 2,075 claims and merge CT-IDs from both sources."""
    logger.info(f"Loading claims from: {CLAIMS_XLSX}")
    wb = openpyxl.load_workbook(str(CLAIMS_XLSX), read_only=True)
    ws = wb["All Claims Combined"]

    # Load newly classified claims
    classified_by_row: Dict[int, Dict] = {}
    if CLASSIFIED_JSON.exists():
        with open(CLASSIFIED_JSON, "r", encoding="utf-8") as f:
            for item in json.load(f):
                if item.get("ct_id") and item["ct_id"] != "FAILED":
                    classified_by_row[item["row"]] = item
        logger.info(f"Loaded {len(classified_by_row)} newly classified claims")

    claims = []
    skipped_no_ct = 0
    for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        claim_text = str(row[4] or "").strip()
        category = str(row[10] or "").strip()
        source_type = str(row[2] or "").strip().lower()

        if not claim_text or len(claim_text) < 20:
            continue
        if category == "Non-claim":
            continue

        # CT-ID: prefer xlsx, fallback to classified JSON
        ct_id = str(row[12] or "").strip()
        picot_data = None

        if not ct_id or len(ct_id) < 3:
            if row_num in classified_by_row:
                ct_id = classified_by_row[row_num]["ct_id"]
                picot_data = classified_by_row[row_num].get("picot")
            else:
                skipped_no_ct += 1
                continue

        # Handle multi-CT (e.g., "CT-301; CT-A08") — use primary
        if ";" in ct_id:
            ct_id = ct_id.split(";")[0].strip()

        claims.append({
            "row": row_num,
            "claim": claim_text,
            "ct_id": ct_id,
            "document": str(row[0] or ""),
            "page": str(row[1] or ""),
            "source_type": source_type,
            "category": category,
            "references": str(row[6] or ""),
            "refers_to": str(row[11] or ""),
            "picot": picot_data,
        })

    wb.close()
    logger.info(f"Loaded {len(claims)} claims ({skipped_no_ct} skipped — no CT-ID)")
    return claims


# ---------------------------------------------------------------------------
# Pipeline initialization (once)
# ---------------------------------------------------------------------------

def init_pipeline(cfg):
    """Initialize all pipeline components — expensive, do once."""
    import torch
    from qdrant_client import QdrantClient
    from transformers import AutoModel, AutoTokenizer

    from new_pipeline.evaluation.logic_gate import LogicGate
    from new_pipeline.evaluation.substantiation_judge import SubstantiationJudge
    from new_pipeline.retrieval.claim_rewriter import ClaimRewriter
    from new_pipeline.retrieval.hybrid_retriever import HybridRetriever
    from new_pipeline.retrieval.mapping_matrix import MappingMatrix

    components = {}

    # Qdrant client
    qdrant = QdrantClient(
        url=cfg.qdrant.url,
        api_key=cfg.qdrant.api_key,
        timeout=30,
    )
    components["qdrant"] = qdrant

    # Mapping matrix
    components["matrix"] = MappingMatrix(mapping_path=cfg.claim_mapping_path)

    # Hybrid retriever
    components["retriever"] = HybridRetriever(
        qdrant_client=qdrant,
        collection_name=cfg.qdrant.collection,
        mapping_matrix=components["matrix"],
    )

    # Claim rewriter
    components["rewriter"] = ClaimRewriter(
        api_key=cfg.llm.anthropic_api_key,
        model=cfg.llm.judge_model,
    )

    # MedCPT query encoder
    cache_dir = os.getenv("HF_HOME", None)
    components["query_tokenizer"] = AutoTokenizer.from_pretrained(
        cfg.embedding.query_model, cache_dir=cache_dir
    )
    components["query_model"] = AutoModel.from_pretrained(
        cfg.embedding.query_model, cache_dir=cache_dir
    ).eval()

    # Judge
    req_path = cfg.substantiation_requirements_path
    req_text = req_path.read_text(encoding="utf-8") if req_path and req_path.exists() else ""
    components["judge"] = SubstantiationJudge(
        api_key=cfg.llm.anthropic_api_key,
        model=cfg.llm.judge_model,
        requirements_text=req_text,
    )

    # Logic gate
    components["logic_gate"] = LogicGate(
        pass_threshold=80.0,
        soft_flag_threshold=60.0,
    )

    return components


def encode_query(query: str, components: dict) -> list[float]:
    """Encode a query string to a MedCPT vector."""
    import torch

    tokenizer = components["query_tokenizer"]
    model = components["query_model"]

    with torch.no_grad():
        encoded = tokenizer(query, return_tensors="pt", max_length=512, truncation=True)
        output = model(**encoded)
        vector = output.last_hidden_state[:, 0, :].squeeze().numpy().tolist()
    return vector


# ---------------------------------------------------------------------------
# Process one claim
# ---------------------------------------------------------------------------

def process_claim(claim_data: dict, components: dict) -> dict:
    """Run the full substantiation pipeline on one claim."""
    from new_pipeline.schemas import CoverageResult, CoverageVerdict, PICOTComponents

    claim_text = claim_data["claim"]
    ct_id = claim_data["ct_id"]
    timings = {}

    # Step 1: Rewrite claim → question
    t = time.time()
    question = components["rewriter"].rewrite(claim_text, ct_id)
    timings["rewrite"] = round(time.time() - t, 2)

    # Step 2: Encode question → vector
    t = time.time()
    query_vector = encode_query(question, components)
    timings["encode"] = round(time.time() - t, 2)

    # Step 3: Hybrid retrieval + cross-encoder re-rank
    t = time.time()
    passages = components["retriever"].search(
        query_vector=query_vector,
        query_text=question,
        ct_id=ct_id,
        original_claim_text=claim_text,
        final_top_k=TOP_K,
    )
    timings["retrieval"] = round(time.time() - t, 2)

    if not passages:
        return {
            "row": claim_data["row"],
            "claim_text": claim_text[:200],
            "ct_id": ct_id,
            "document": claim_data["document"],
            "verdict": CoverageVerdict.BLOCK.value,
            "coverage": 0,
            "passages": 0,
            "timings": timings,
            "error": "No passages found",
        }

    # Step 4: Judge evaluation
    t = time.time()
    picot = claim_data.get("picot") or {}
    picot_obj = PICOTComponents(
        population=picot.get("population"),
        intervention=picot.get("intervention"),
        comparator=picot.get("comparator"),
        outcome=picot.get("outcome"),
        timeframe=picot.get("timeframe"),
    )

    coverage_result, judge_raw = components["judge"].evaluate(
        claim_text=claim_text,
        ct_id=ct_id,
        picot=picot_obj,
        passages=passages,
    )
    timings["judge"] = round(time.time() - t, 2)

    # Step 5: Logic gate
    t = time.time()
    verdict = components["logic_gate"].evaluate(
        coverage_result=coverage_result,
        judge_raw=judge_raw,
        claim_ct_id=ct_id,
    )
    timings["logic_gate"] = round(time.time() - t, 4)

    total_time = sum(timings.values())

    return {
        "row": claim_data["row"],
        "claim_text": claim_text[:200],
        "ct_id": ct_id,
        "document": claim_data["document"],
        "category": claim_data.get("category", ""),
        "verdict": verdict["verdict"],
        "coverage": verdict["coverage_score"],
        "flags": verdict.get("flags", []),
        "blockers": verdict.get("blockers", []),
        "passages": len(passages),
        "top_ref": passages[0].get("ref_id", "") if passages else "",
        "timings": timings,
        "total_time": round(total_time, 1),
    }


# ---------------------------------------------------------------------------
# Portfolio report
# ---------------------------------------------------------------------------

def generate_report(results: list[dict], output_path: Path) -> None:
    """Generate portfolio-level coverage summary (Section 3.4)."""
    # Overall stats
    total = len(results)
    pass_count = sum(1 for r in results if r["verdict"] == "pass")
    soft_count = sum(1 for r in results if r["verdict"] == "soft_flag")
    block_count = sum(1 for r in results if r["verdict"] == "block")
    scores = [r["coverage"] for r in results if isinstance(r["coverage"], (int, float))]
    mean_score = sum(scores) / len(scores) if scores else 0

    # Per-document breakdown
    by_doc: Dict[str, List[Dict]] = defaultdict(list)
    for r in results:
        by_doc[r.get("document", "Unknown")].append(r)

    # Per-CT breakdown
    by_ct: Dict[str, List[Dict]] = defaultdict(list)
    for r in results:
        by_ct[r.get("ct_id", "Unknown")].append(r)

    lines = [
        "# Portfolio Coverage Report",
        "",
        f"*Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
        "---",
        "",
        "## Overall Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total claims | **{total}** |",
        f"| Fully covered (≥80%) | **{pass_count}** ({pass_count*100//total}%) |",
        f"| Partially covered (60-79%) | **{soft_count}** ({soft_count*100//total}%) |",
        f"| Uncovered (<60%) | **{block_count}** ({block_count*100//total}%) |",
        f"| Mean coverage score | **{mean_score:.1f}%** |",
        "",
        "---",
        "",
        "## Per-Document Breakdown",
        "",
        "| Document | Claims | Pass | Soft | Block | Mean |",
        "|----------|-------:|-----:|-----:|------:|-----:|",
    ]

    for doc in sorted(by_doc.keys()):
        doc_results = by_doc[doc]
        n = len(doc_results)
        p = sum(1 for r in doc_results if r["verdict"] == "pass")
        s = sum(1 for r in doc_results if r["verdict"] == "soft_flag")
        b = sum(1 for r in doc_results if r["verdict"] == "block")
        doc_scores = [r["coverage"] for r in doc_results if isinstance(r["coverage"], (int, float))]
        m = sum(doc_scores) / len(doc_scores) if doc_scores else 0
        doc_short = doc[:50] + "..." if len(doc) > 50 else doc
        lines.append(f"| {doc_short} | {n} | {p} | {s} | {b} | {m:.0f}% |")

    lines += [
        "",
        "---",
        "",
        "## Per-Claim-Type Breakdown",
        "",
        "| CT-ID | Claims | Pass | Soft | Block | Mean |",
        "|-------|-------:|-----:|-----:|------:|-----:|",
    ]

    for ct in sorted(by_ct.keys()):
        ct_results = by_ct[ct]
        n = len(ct_results)
        p = sum(1 for r in ct_results if r["verdict"] == "pass")
        s = sum(1 for r in ct_results if r["verdict"] == "soft_flag")
        b = sum(1 for r in ct_results if r["verdict"] == "block")
        ct_scores = [r["coverage"] for r in ct_results if isinstance(r["coverage"], (int, float))]
        m = sum(ct_scores) / len(ct_scores) if ct_scores else 0
        lines.append(f"| {ct} | {n} | {p} | {s} | {b} | {m:.0f}% |")

    # Blocked claims detail
    blocked = [r for r in results if r["verdict"] == "block"]
    if blocked:
        lines += [
            "",
            "---",
            "",
            "## Blocked Claims (Require Re-substantiation)",
            "",
            "| Row | CT-ID | Document | Coverage | Blocker |",
            "|----:|-------|----------|:--------:|---------|",
        ]
        for r in blocked[:100]:  # Show first 100
            blockers = "; ".join(r.get("blockers", ["Coverage too low"]))[:60]
            doc_short = r.get("document", "")[:30]
            lines.append(
                f"| {r['row']} | {r['ct_id']} | {doc_short} | {r['coverage']:.0f}% | {blockers} |"
            )

    report = "\n".join(lines)
    output_path.write_text(report, encoding="utf-8")
    logger.info(f"Portfolio report saved to {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    os.environ.setdefault("HF_HOME", r"D:\hf_cache")
    os.environ.setdefault("TRANSFORMERS_CACHE", r"D:\hf_cache")

    cfg = load_config()

    # Load all claims
    claims = load_all_claims()
    if not claims:
        logger.error("No claims loaded!")
        return

    # Load existing results for resume
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    existing_results: List[Dict] = []
    done_rows: set = set()
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            existing_results = json.load(f)
        done_rows = {r["row"] for r in existing_results}
        logger.info(f"Resuming: {len(done_rows)} claims already processed")

    to_process = [c for c in claims if c["row"] not in done_rows]
    logger.info(f"Claims to process: {len(to_process)} / {len(claims)}")

    if not to_process:
        logger.info("All claims already processed!")
        generate_report(existing_results, REPORT_FILE)
        return

    # Initialize pipeline (expensive — do once)
    logger.info("Initializing pipeline components...")
    components = init_pipeline(cfg)
    logger.info("Pipeline ready")

    # Process claims
    all_results = list(existing_results)
    start_time = time.time()
    errors = 0

    for i, claim_data in enumerate(to_process, 1):
        try:
            result = process_claim(claim_data, components)
            all_results.append(result)

            # Progress
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            remaining = (len(to_process) - i) / rate if rate > 0 else 0
            logger.info(
                f"[{i}/{len(to_process)}] Row {claim_data['row']}: "
                f"{result['verdict'].upper()} {result['coverage']:.0f}% "
                f"({result['total_time']:.1f}s) | "
                f"ETA: {remaining/60:.0f}min"
            )

        except Exception as e:
            errors += 1
            logger.error(f"[{i}/{len(to_process)}] Row {claim_data['row']}: ERROR - {e}")
            all_results.append({
                "row": claim_data["row"],
                "claim_text": claim_data["claim"][:200],
                "ct_id": claim_data["ct_id"],
                "document": claim_data["document"],
                "verdict": "error",
                "coverage": 0,
                "error": str(e),
            })

        # Checkpoint every 50 claims
        if i % 50 == 0:
            with open(RESULTS_FILE, "w", encoding="utf-8") as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)
            logger.info(f"Checkpoint saved ({len(all_results)} results)")

    # Final save
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    # Generate portfolio report
    generate_report(all_results, REPORT_FILE)

    # Summary
    elapsed = time.time() - start_time
    verdicts = defaultdict(int)
    for r in all_results:
        verdicts[r.get("verdict", "error")] += 1

    print(f"\n{'='*60}")
    print(f"BATCH SUBSTANTIATION COMPLETE")
    print(f"{'='*60}")
    print(f"Total processed: {len(all_results)}")
    print(f"Time: {elapsed:.0f}s ({elapsed/60:.1f}min)")
    print(f"Errors: {errors}")
    print(f"\nVerdicts:")
    for v, c in sorted(verdicts.items()):
        print(f"  {v:12s}: {c:4d}")
    print(f"\nResults: {RESULTS_FILE}")
    print(f"Report:  {REPORT_FILE}")


if __name__ == "__main__":
    main()
