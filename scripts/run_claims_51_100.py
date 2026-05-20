#!/usr/bin/env python3
"""Run claims 51-100 through full substantiation pipeline → MD report.

Skips the first 50 unique claims (already tested), then processes the NEXT 50.
Same pipeline: Dense(MedCPT) + BM25(fastembed) + AND-match keywords → Claude Sonnet 4.6 judge.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Stub onnxruntime before any fastembed import (BM25 doesn't need ONNX)
import types as _types
import importlib as _il
_ort = _types.ModuleType("onnxruntime")
_ort.__spec__ = _il.machinery.ModuleSpec("onnxruntime", None)
_ort.SessionOptions = type("SessionOptions", (), {})
_ort.InferenceSession = type("InferenceSession", (), {})
_ort.GraphOptimizationLevel = type("GraphOptimizationLevel", (), {"ORT_ENABLE_ALL": 99})

_ort_capi = _types.ModuleType("onnxruntime.capi")
_ort_capi.__spec__ = _il.machinery.ModuleSpec("onnxruntime.capi", None)
_ort_pybind = _types.ModuleType("onnxruntime.capi._pybind_state")
_ort_pybind.__spec__ = _il.machinery.ModuleSpec("onnxruntime.capi._pybind_state", None)

sys.modules["onnxruntime"] = _ort
sys.modules["onnxruntime.capi"] = _ort_capi
sys.modules["onnxruntime.capi._pybind_state"] = _ort_pybind
sys.path.insert(0, "D:\\pip_packages")

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env", override=True)

os.environ["HF_HOME"] = r"D:\hf_cache"
os.environ["TRANSFORMERS_CACHE"] = r"D:\hf_cache"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import openpyxl
from collections import Counter
from qdrant_client import QdrantClient

from new_pipeline.config import load_config
from new_pipeline.retrieval.hybrid_retriever import HybridRetriever
from new_pipeline.retrieval.mapping_matrix import MappingMatrix
from new_pipeline.retrieval.claim_rewriter import ClaimRewriter
from new_pipeline.evaluation.substantiation_judge import SubstantiationJudge
from new_pipeline.schemas import ClaimClassification, PICOTComponents
from transformers import AutoTokenizer, AutoModel
import torch

logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

OUTPUT_MD = Path(__file__).parent.parent / "claims" / "claims_51_100_results.md"


def load_claims_range(cfg, skip=50, limit=50):
    """Load claims, skip the first `skip` unique ones, return the next `limit`."""
    xlsx = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\claims\ALL_CLAIMS_COMBINED_categorized_v5.xlsx")
    wb = openpyxl.load_workbook(str(xlsx), read_only=True)
    ws = wb["All Claims Combined"]

    # Load newly classified CT-IDs
    classified_path = xlsx.parent / "classified_missing_claims.json"
    classified_map = {}
    if classified_path.exists():
        for item in json.loads(classified_path.read_text(encoding="utf-8")):
            classified_map[item["row"]] = item

    seen_texts = set()
    skipped = 0
    claims = []

    for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        claim = str(row[4] or "").strip()
        category = str(row[10] or "").strip()
        ct_id = str(row[12] or "").strip()
        doc = str(row[0] or "").strip()

        if not claim or len(claim) < 20 or category == "Non-claim":
            continue

        # Use classified CT-ID if xlsx is empty
        ct_name = ""
        if (not ct_id or len(ct_id) < 3) and row_num in classified_map:
            ct_id = classified_map[row_num].get("ct_id", "")
            ct_name = classified_map[row_num].get("claim_type_name", "")

        if claim in seen_texts:
            continue
        seen_texts.add(claim)

        if ct_id and len(ct_id) >= 3:
            # Skip the first N unique claims
            if skipped < skip:
                skipped += 1
                continue

            claims.append({
                "row": row_num,
                "claim": claim,
                "ct_id": ct_id,
                "ct_name": ct_name,
                "document": doc,
            })

        if len(claims) >= limit:
            break

    wb.close()
    logger.info(f"Skipped {skipped} claims, loaded {len(claims)} new claims (rows {claims[0]['row']}-{claims[-1]['row']})")
    return claims


def main():
    cfg = load_config()

    claims = load_claims_range(cfg, skip=50, limit=50)
    logger.info(f"Loaded {len(claims)} claims for batch 51-100")

    # Init Qdrant
    qdrant = QdrantClient(url=cfg.qdrant.url, api_key=cfg.qdrant.api_key, timeout=30)

    # Init components
    matrix = MappingMatrix(cfg.claim_mapping_path)

    # Init query encoder FIRST (most memory-hungry)
    import gc
    gc.collect()
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    import ctypes
    try:
        ctypes.windll.kernel32.SetProcessWorkingSetSize(-1, -1, -1)
    except:
        pass
    logger.info("Loading MedCPT query encoder...")
    q_tokenizer = AutoTokenizer.from_pretrained("ncbi/MedCPT-Query-Encoder", cache_dir=r"D:\hf_cache")
    q_model = AutoModel.from_pretrained("ncbi/MedCPT-Query-Encoder", cache_dir=r"D:\hf_cache", low_cpu_mem_usage=True)
    q_model.eval()
    q_model.half()
    logger.info("MedCPT ready (float16)")

    # Load BM25 model (lightweight CPU tokenizer — minimal memory)
    from fastembed.sparse.bm25 import Bm25
    logger.info("Loading fastembed BM25 model...")
    bm25_model = Bm25(model_name="Qdrant/bm25", cache_dir=r"D:\hf_cache")
    logger.info("BM25 model ready")

    rewriter = ClaimRewriter(
        provider="openai",
        model="gpt-5.2",
        api_key=cfg.llm.openai_api_key,
    )

    judge = SubstantiationJudge(
        api_key=cfg.llm.anthropic_api_key,
        model="claude-sonnet-4-6",
        requirements_path=cfg.substantiation_requirements_path,
    )

    retriever = HybridRetriever(
        qdrant_client=qdrant,
        collection_name=cfg.qdrant.collection_name,
        mapping_matrix=matrix,
        bm25_model=bm25_model,
    )


    def encode_query(text: str) -> list:
        with torch.no_grad():
            encoded = q_tokenizer(text, max_length=64, truncation=True, padding=True, return_tensors="pt")
            emb = q_model(**encoded).last_hidden_state[:, 0, :]
            return emb[0].tolist()

    results = []
    start = time.time()
    total = len(claims)

    for i, claim_data in enumerate(claims, 1):
        claim_text = claim_data["claim"]
        ct_id = claim_data["ct_id"]
        t0 = time.time()

        try:
            # Step 1: Rewrite
            question = rewriter.rewrite(claim_text)

            # Step 2: Encode + Retrieve (3 signals: dense + BM25 + AND-match)
            query_vec = encode_query(question)
            passages = retriever.search(
                query_vector=query_vec,
                query_text=question,
                bm25_query_text=claim_text,
                ct_id=ct_id,
                final_top_k=20,
            )

            # Step 3: Judge
            classification = ClaimClassification(
                ct_id=ct_id,
                claim_type_name=claim_data.get("ct_name", ct_id),
                confidence=0.9,
            )
            picot = PICOTComponents()

            if passages:
                raw = judge.evaluate(
                    claim_text=claim_text,
                    classification=classification,
                    picot=picot,
                    evidence_passages=passages[:15],
                )
            else:
                raw = {
                    "coverage_score": 0,
                    "overall_assessment": "No passages retrieved.",
                    "sub_assertions": [],
                }

            coverage = raw.get("coverage_score", 0)
            if isinstance(coverage, str):
                try:
                    coverage = float(coverage.replace("%", ""))
                except:
                    coverage = 0

            if coverage >= 80:
                verdict = "PASS"
            elif coverage >= 60:
                verdict = "SOFT_FLAG"
            else:
                verdict = "BLOCK"

            elapsed = time.time() - t0

            result = {
                "idx": i + 50,  # Global index: 51-100
                "row": claim_data["row"],
                "claim": claim_text,
                "ct_id": ct_id,
                "document": claim_data["document"],
                "question": question,
                "num_passages": len(passages),
                "top_passage_score": round(passages[0]["final_score"], 3) if passages else 0,
                "top_passage_rt_id": passages[0].get("rt_id", "?") if passages else "?",
                "top_passage_ref": passages[0].get("ref_id", "?") if passages else "?",
                "top_passage_tier": passages[0].get("tier", "?") if passages else "?",
                "verdict": verdict,
                "coverage": coverage,
                "assessment": raw.get("overall_assessment", ""),
                "sub_assertions": raw.get("sub_assertions", []),
                "time_s": round(elapsed, 1),
                "passage_summaries": [
                    {
                        "rank": j + 1,
                        "ref_id": p.get("ref_id", "?")[:55],
                        "rt_id": p.get("rt_id", "?"),
                        "tier": p.get("tier", "?"),
                        "score": round(p.get("final_score", 0), 4),
                        "product_boost": p.get("product_boost", False),
                        "preview": p.get("text", "")[:80].replace("\n", " "),
                    }
                    for j, p in enumerate(passages[:15])
                ],
            }
            results.append(result)

            emoji = {"PASS": "✅", "SOFT_FLAG": "⚠️", "BLOCK": "❌"}.get(verdict, "❓")
            logger.info(
                f"  [{i}/{total}] {emoji} {verdict} ({coverage}%) "
                f"| {ct_id} | {elapsed:.1f}s | {claim_text[:60]}..."
            )

        except Exception as e:
            elapsed = time.time() - t0
            results.append({
                "idx": i + 50,
                "row": claim_data["row"],
                "claim": claim_text,
                "ct_id": ct_id,
                "document": claim_data["document"],
                "verdict": "ERROR",
                "coverage": 0,
                "assessment": str(e),
                "time_s": round(elapsed, 1),
            })
            logger.error(f"  [{i}/{total}] ERROR: {e}")

    total_time = time.time() - start

    # ── Build MD Report ──
    md = []
    md.append("# Claims 51–100 — Substantiation Results\n")
    md.append(f"**Date:** {time.strftime('%Y-%m-%d %H:%M')}")
    md.append(f"**Total time:** {total_time:.0f}s ({total_time/60:.1f} min)")
    md.append(f"**Average per claim:** {total_time/len(results):.1f}s\n")

    vc = Counter(r["verdict"] for r in results)
    coverages = [r.get("coverage", 0) for r in results]
    avg_cov = sum(coverages) / len(coverages) if coverages else 0

    md.append("## Summary\n")
    md.append("| Verdict | Count | % |")
    md.append("|---------|------:|--:|")
    for v in ["PASS", "SOFT_FLAG", "BLOCK", "ERROR"]:
        if v in vc:
            pct = vc[v] / len(results) * 100
            emoji = {"PASS": "✅", "SOFT_FLAG": "⚠️", "BLOCK": "❌", "ERROR": "❓"}[v]
            md.append(f"| {emoji} {v} | {vc[v]} | {pct:.0f}% |")
    md.append(f"| **Total** | **{len(results)}** | **100%** |")
    md.append(f"\n**Average coverage:** {avg_cov:.0f}%\n")

    md.append("---\n")
    md.append("## Detailed Results\n")

    for r in results:
        emoji = {"PASS": "✅", "SOFT_FLAG": "⚠️", "BLOCK": "❌", "ERROR": "❓"}.get(r["verdict"], "❓")
        md.append(f"### #{r['idx']} (Row {r['row']}) — {emoji} {r['verdict']} ({r.get('coverage', 0)}%)\n")
        md.append(f"- **CT-ID:** `{r['ct_id']}` | **Time:** {r['time_s']}s")
        md.append(f"- **Document:** {r.get('document', '')[:70]}")
        md.append(f"- **Claim:** {r['claim'][:300]}\n")

        if r.get("question"):
            md.append(f"- **Search query:** {r['question']}\n")

        if r.get("top_passage_ref"):
            md.append(f"- **Top match:** `{r.get('top_passage_rt_id', '?')}` (tier: {r.get('top_passage_tier', '?')}) from `{r.get('top_passage_ref', '?')[:55]}` (score: {r.get('top_passage_score', 0)})\n")

        subs = r.get("sub_assertions", [])
        if subs:
            md.append("**Sub-assertions:**\n")
            for sa in subs:
                covered = sa.get("is_covered", False)
                icon = "✅" if covered else "❌"
                text = sa.get("sub_assertion", "?")
                evidence = sa.get("evidence_text", "")
                md.append(f"- {icon} {text}")
                if evidence and covered:
                    md.append(f"  > *\"{evidence[:150]}\"*")
            md.append("")

        if r.get("assessment"):
            md.append(f"**Assessment:** {r['assessment'][:400]}\n")

        # For non-PASS verdicts, show ALL passages the judge received
        psums = r.get("passage_summaries", [])
        if psums and r.get("verdict") in ("BLOCK", "SOFT_FLAG", "ERROR"):
            md.append("<details><summary>📋 All passages sent to judge</summary>\n")
            md.append("| # | RT-ID | Tier | Score | Boosted | ref_id | Preview |")
            md.append("|---|-------|------|-------|---------|--------|---------|")
            for ps in psums:
                boost_icon = "🚀" if ps.get("product_boost") else ""
                md.append(
                    f"| {ps['rank']} | `{ps['rt_id']}` | {ps['tier']} "
                    f"| {ps['score']} | {boost_icon} "
                    f"| {ps['ref_id'][:40]} | {ps['preview'][:60]} |"
                )
            md.append("\n</details>\n")

        md.append("---\n")

    OUTPUT_MD.write_text("\n".join(md), encoding="utf-8")
    logger.info(f"Report written to: {OUTPUT_MD}")

    print(f"\n{'='*60}")
    print(f"COMPLETE: {len(results)} claims substantiated in {total_time:.0f}s")
    print(f"  PASS: {vc.get('PASS',0)} | SOFT_FLAG: {vc.get('SOFT_FLAG',0)} | BLOCK: {vc.get('BLOCK',0)}")
    print(f"  Avg coverage: {avg_cov:.0f}%")
    print(f"  Report: {OUTPUT_MD}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
