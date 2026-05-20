#!/usr/bin/env python3
"""Re-run ONLY the 8 blocked claims with fixes: markdown strip + product boost + Sonnet 4.6.
Also logs the FULL passage list sent to judge for diagnosis."""

import json, logging, os, sys, time, gc, re
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Stub onnxruntime
import types as _types, importlib as _il
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

# The 8 claims that were BLOCKED in the previous run
BLOCKED_CLAIMS = [
    {"idx": 2,  "row": 5,  "ct_id": "CT-603", "claim": "You should not inject VYVGART HYTRULO into a vein or muscle."},
    {"idx": 5,  "row": 9,  "ct_id": "CT-604", "claim": "A novel treatment for adult patients with chronic inflammatory demyelinating polyneuropathy (CIDP)"},
    {"idx": 7,  "row": 11, "ct_id": "CT-605", "claim": "Do not share the prefilled syringe."},
    {"idx": 10, "row": 14, "ct_id": "CT-606", "claim": "Do not freeze VYVGART HYTRULO."},
    {"idx": 21, "row": 39, "ct_id": "CT-605", "claim": "Discard any unused portion"},
    {"idx": 33, "row": 52, "ct_id": "CT-606", "claim": "Do not attempt to warm the prefilled syringe in any other way."},
    {"idx": 34, "row": 53, "ct_id": "CT-606", "claim": "Do not attempt to warm the filled syringe in any other way."},
    {"idx": 50, "row": 75, "ct_id": "CT-603", "claim": "Do not inject into a vein."},
]

OUTPUT_MD = Path(__file__).parent.parent / "claims" / "blocked_rerun_results.md"


def main():
    cfg = load_config()

    qdrant = QdrantClient(url=cfg.qdrant.url, api_key=cfg.qdrant.api_key, timeout=30)
    matrix = MappingMatrix(cfg.claim_mapping_path)

    from fastembed.sparse.bm25 import Bm25
    logger.info("Loading BM25...")
    bm25_model = Bm25(model_name="Qdrant/bm25", cache_dir=r"D:\hf_cache")

    retriever = HybridRetriever(
        qdrant_client=qdrant,
        collection_name=cfg.qdrant.collection_name,
        mapping_matrix=matrix,
        bm25_model=bm25_model,
    )

    rewriter = ClaimRewriter(provider="openai", model="gpt-5.2", api_key=cfg.llm.openai_api_key)

    judge = SubstantiationJudge(
        api_key=cfg.llm.anthropic_api_key,
        model="claude-sonnet-4-6",
        requirements_path=cfg.substantiation_requirements_path,
    )

    gc.collect()
    logger.info("Loading MedCPT...")
    q_tokenizer = AutoTokenizer.from_pretrained("ncbi/MedCPT-Query-Encoder")
    q_model = AutoModel.from_pretrained("ncbi/MedCPT-Query-Encoder")
    q_model.eval().half()
    logger.info("MedCPT ready")

    def encode_query(text):
        with torch.no_grad():
            enc = q_tokenizer(text, max_length=64, truncation=True, padding=True, return_tensors="pt")
            emb = q_model(**enc).last_hidden_state[:, 0, :]
            return emb[0].tolist()

    md = ["# Blocked Claims Re-run — Sonnet 4.6 + Markdown Strip + Product Boost\n"]
    md.append(f"**Date:** {time.strftime('%Y-%m-%d %H:%M')}\n")

    for claim_data in BLOCKED_CLAIMS:
        claim_text = claim_data["claim"]
        ct_id = claim_data["ct_id"]
        idx = claim_data["idx"]
        t0 = time.time()

        logger.info(f"\n{'='*60}")
        logger.info(f"  Claim #{idx}: {claim_text[:70]}...")
        logger.info(f"{'='*60}")

        try:
            # Step 1: Rewrite
            question = rewriter.rewrite(claim_text)
            logger.info(f"  Rewritten: {question[:80]}")

            # Step 2: Retrieve
            query_vec = encode_query(question)
            passages = retriever.search(
                query_vector=query_vec,
                query_text=question,
                bm25_query_text=claim_text,
                ct_id=ct_id,
                final_top_k=20,
            )

            # DIAGNOSTIC: Check if evidence exists in passages
            logger.info(f"  Retrieved {len(passages)} passages")
            has_vyvgart_pi = False
            for j, p in enumerate(passages[:15]):
                ref = p.get("ref_id", "")
                rt = p.get("rt_id", "")
                score = p.get("final_score", 0)
                boost = p.get("product_boost", False)
                text_preview = p.get("text", "")[:100].replace("\n", " ")
                if "vyvgart" in ref.lower():
                    has_vyvgart_pi = True
                logger.info(f"    [{j+1}] rt={rt} score={score:.4f} boost={boost} | {ref[:45]}")

            # Step 3: Judge
            classification = ClaimClassification(ct_id=ct_id, claim_type_name=ct_id, confidence=0.9)
            picot = PICOTComponents()

            if passages:
                raw = judge.evaluate(
                    claim_text=claim_text,
                    classification=classification,
                    picot=picot,
                    evidence_passages=passages[:15],
                )
            else:
                raw = {"coverage_score": 0, "overall_assessment": "No passages.", "sub_assertions": []}

            coverage = raw.get("coverage_score", 0)
            if isinstance(coverage, str):
                try: coverage = float(coverage.replace("%", ""))
                except: coverage = 0

            if coverage >= 80: verdict = "PASS"
            elif coverage >= 60: verdict = "SOFT_FLAG"
            else: verdict = "BLOCK"

            elapsed = time.time() - t0
            emoji = {"PASS": "✅", "SOFT_FLAG": "⚠️", "BLOCK": "❌"}.get(verdict, "❓")
            logger.info(f"  → {emoji} {verdict} ({coverage}%) in {elapsed:.1f}s")

            # Build MD
            md.append(f"## #{idx} (Row {claim_data['row']}) — {emoji} {verdict} ({coverage}%)\n")
            md.append(f"- **CT-ID:** `{ct_id}` | **Time:** {elapsed:.1f}s")
            md.append(f"- **Claim:** {claim_text}")
            md.append(f"- **Search query:** {question}")
            md.append(f"- **VYVGART PI in top 15?** {'✅ Yes' if has_vyvgart_pi else '❌ No'}\n")

            # Passage table
            md.append("**All 15 passages sent to judge:**\n")
            md.append("| # | RT-ID | Tier | Score | Boost | ref_id | Preview |")
            md.append("|---|-------|------|-------|-------|--------|---------|")
            for j, p in enumerate(passages[:15]):
                boost_icon = "🚀" if p.get("product_boost") else ""
                preview = p.get("text", "")[:70].replace("\n", " ").replace("|", "/")
                md.append(
                    f"| {j+1} | `{p.get('rt_id','?')}` | {p.get('tier','?')} "
                    f"| {p.get('final_score',0):.4f} | {boost_icon} "
                    f"| {p.get('ref_id','?')[:40]} | {preview} |"
                )
            md.append("")

            # Sub-assertions
            subs = raw.get("sub_assertions", [])
            if subs:
                md.append("**Sub-assertions:**\n")
                for sa in subs:
                    covered = sa.get("is_covered", False)
                    icon = "✅" if covered else "❌"
                    text = sa.get("sub_assertion", "?")
                    evidence = sa.get("evidence_text", "")
                    md.append(f"- {icon} {text}")
                    if evidence and covered:
                        md.append(f'  > *"{evidence[:150]}"*')
                md.append("")

            if raw.get("overall_assessment"):
                md.append(f"**Assessment:** {raw['overall_assessment'][:500]}\n")

            md.append("---\n")

        except Exception as e:
            logger.error(f"  ERROR: {e}")
            md.append(f"## #{idx} — ❓ ERROR\n- {str(e)}\n---\n")

    OUTPUT_MD.write_text("\n".join(md), encoding="utf-8")
    logger.info(f"\nReport: {OUTPUT_MD}")
    print(f"\nDONE — report at {OUTPUT_MD}")


if __name__ == "__main__":
    main()
