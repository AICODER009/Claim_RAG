#!/usr/bin/env python3
"""Deep diagnosis: For each remaining BLOCK, find the exact chunk with evidence,
check its dense rank, BM25 rank, and whether it makes top 15 after fusion."""

import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "D:\\pip_packages")
sys.path.insert(0, "D:\\revisto_evidence_aligned_clean")

import types as _types, importlib as _il
_ort = _types.ModuleType("onnxruntime")
_ort.__spec__ = _il.machinery.ModuleSpec("onnxruntime", None)
_ort.SessionOptions = type("SessionOptions", (), {})
_ort.InferenceSession = type("InferenceSession", (), {})
_ort.GraphOptimizationLevel = type("GraphOptimizationLevel", (), {"ORT_ENABLE_ALL": 99})
sys.modules["onnxruntime"] = _ort
_ort_capi = _types.ModuleType("onnxruntime.capi")
_ort_capi.__spec__ = _il.machinery.ModuleSpec("onnxruntime.capi", None)
_ort_pybind = _types.ModuleType("onnxruntime.capi._pybind_state")
_ort_pybind.__spec__ = _il.machinery.ModuleSpec("onnxruntime.capi._pybind_state", None)
sys.modules["onnxruntime.capi"] = _ort_capi
sys.modules["onnxruntime.capi._pybind_state"] = _ort_pybind

from dotenv import load_dotenv
from pathlib import Path
load_dotenv("D:/revisto_evidence_aligned_clean/new_pipeline/.env", override=True)
os.environ["HF_HOME"] = r"D:\hf_cache"

from qdrant_client import QdrantClient, models
from new_pipeline.config import load_config
import gc, torch

cfg = load_config()
c = QdrantClient(url=cfg.qdrant.url, api_key=cfg.qdrant.api_key, timeout=30)
col = cfg.qdrant.collection_name
bm25_col = "verifai_mlr_bm25"

# ── 1. Find the exact chunks that contain the evidence ──
CASES = [
    {
        "label": "BLOCK #21: 'Discard any unused portion'",
        "claim": "Discard any unused portion",
        "search_terms": ["Discard"],
        "target_ref": "vyvgart",  # We want VYVGART PI
    },
    {
        "label": "BLOCK #33: 'Do not attempt to warm the prefilled syringe in any other way'",
        "claim": "Do not attempt to warm the prefilled syringe in any other way.",
        "search_terms": ["Do not attempt to warm", "any other way"],
        "target_ref": "vyvgart",
    },
    {
        "label": "BLOCK #34: 'Do not attempt to warm the filled syringe in any other way'",
        "claim": "Do not attempt to warm the filled syringe in any other way.",
        "search_terms": ["Do not attempt to warm", "any other way"],
        "target_ref": "vyvgart",
    },
]

print("=" * 80)
print("STEP 1: Find chunks containing the evidence text")
print("=" * 80)

target_point_ids = {}  # case_label -> list of point IDs

for case in CASES:
    print(f"\n{'─'*70}")
    print(f"  {case['label']}")
    print(f"{'─'*70}")

    for term in case["search_terms"]:
        res = c.scroll(
            collection_name=col,
            scroll_filter=models.Filter(
                must=[models.FieldCondition(key="text", match=models.MatchText(text=term))]
            ),
            limit=20,
            with_payload=["text", "ref_id", "rt_id", "section"],
        )

        vyvgart_hits = []
        other_hits = []
        for pt in res[0]:
            ref = (pt.payload.get("ref_id") or "").lower()
            is_target = case["target_ref"] in ref
            info = {
                "id": pt.id,
                "ref_id": pt.payload.get("ref_id", "?")[:55],
                "rt_id": pt.payload.get("rt_id", "?"),
                "section": pt.payload.get("section", "?")[:60],
            }
            # Find the matching line
            for line in pt.payload.get("text", "").split("\n"):
                if term.lower() in line.lower():
                    info["match_line"] = line.strip()[:140]
                    break
            else:
                info["match_line"] = "(term in chunk, no single line)"

            if is_target:
                vyvgart_hits.append(info)
            else:
                other_hits.append(info)

        print(f"\n  Term: '{term}'")
        print(f"  VYVGART hits: {len(vyvgart_hits)}")
        for h in vyvgart_hits:
            print(f"    ID={h['id']} | rt={h['rt_id']} | section={h['section']}")
            print(f"      >> \"{h['match_line']}\"")
            target_point_ids.setdefault(case["label"], []).append(h["id"])

        print(f"  Other product hits: {len(other_hits)}")
        for h in other_hits[:3]:
            print(f"    ID={h['id']} | rt={h['rt_id']} | ref={h['ref_id']}")


# ── 2. Check dense ranking of target chunks ──
print(f"\n\n{'='*80}")
print("STEP 2: Check dense ranking of target chunks")
print("='*80")

from transformers import AutoTokenizer, AutoModel

gc.collect()
q_tokenizer = AutoTokenizer.from_pretrained("ncbi/MedCPT-Query-Encoder")
q_model = AutoModel.from_pretrained("ncbi/MedCPT-Query-Encoder")
q_model.eval().half()

from new_pipeline.retrieval.claim_rewriter import ClaimRewriter
rewriter = ClaimRewriter(provider="openai", model="gpt-5.2", api_key=cfg.llm.openai_api_key)

def encode_query(text):
    with torch.no_grad():
        enc = q_tokenizer(text, max_length=64, truncation=True, padding=True, return_tensors="pt")
        emb = q_model(**enc).last_hidden_state[:, 0, :]
        return emb[0].tolist()

for case in CASES:
    print(f"\n{'─'*70}")
    print(f"  {case['label']}")
    print(f"{'─'*70}")

    claim = case["claim"]
    question = rewriter.rewrite(claim)
    query_vec = encode_query(question)

    print(f"  Claim: {claim}")
    print(f"  Rewritten: {question}")

    # Dense search — get top 300 to find rank
    dense_results = c.query_points(
        collection_name=col,
        query=query_vec,
        limit=300,
        with_payload=["ref_id", "rt_id", "section"],
    )

    target_ids = set(target_point_ids.get(case["label"], []))
    found_rank = None
    for rank, pt in enumerate(dense_results.points, 1):
        if pt.id in target_ids:
            ref = pt.payload.get("ref_id", "?")[:50]
            sec = pt.payload.get("section", "?")[:50]
            print(f"  Dense rank: #{rank} | score={pt.score:.4f} | ref={ref} | section={sec}")
            if found_rank is None:
                found_rank = rank

    if found_rank is None:
        print(f"  Dense rank: NOT IN TOP 300!")

    # Show top 3 dense results
    print(f"  Dense top 3:")
    for i, pt in enumerate(dense_results.points[:3], 1):
        ref = pt.payload.get("ref_id", "?")[:45]
        print(f"    #{i}: score={pt.score:.4f} | {ref} | {pt.payload.get('section', '?')[:50]}")

    # ── 3. BM25 search ──
    from fastembed.sparse.bm25 import Bm25
    bm25_model = Bm25(model_name="Qdrant/bm25", cache_dir=r"D:\hf_cache")

    # BM25 encode the original claim
    sparse_vecs = list(bm25_model.query_embed(claim))
    if sparse_vecs:
        sv = sparse_vecs[0]
        indices = sv.indices.tolist()
        values = sv.values.tolist()

        bm25_results = c.query_points(
            collection_name=bm25_col,
            query=models.SparseVector(indices=indices, values=values),
            using="bm25",
            limit=100,
            with_payload=["ref_id", "rt_id", "section"],
        )

        bm25_found_rank = None
        for rank, pt in enumerate(bm25_results.points, 1):
            if pt.id in target_ids:
                ref = pt.payload.get("ref_id", "?")[:50]
                sec = pt.payload.get("section", "?")[:50]
                print(f"  BM25 rank: #{rank} | score={pt.score:.4f} | ref={ref} | section={sec}")
                if bm25_found_rank is None:
                    bm25_found_rank = rank

        if bm25_found_rank is None:
            print(f"  BM25 rank: NOT IN TOP 100!")

        print(f"  BM25 top 3:")
        for i, pt in enumerate(bm25_results.points[:3], 1):
            ref = pt.payload.get("ref_id", "?")[:45]
            print(f"    #{i}: score={pt.score:.4f} | {ref} | {pt.payload.get('section', '?')[:50]}")

    # Break after first BM25 model load
    break  # BM25 model loaded once, reuse below

# Run remaining cases with BM25 already loaded
for case in CASES[1:]:
    print(f"\n{'─'*70}")
    print(f"  {case['label']} — BM25 check")
    print(f"{'─'*70}")
    claim = case["claim"]
    target_ids = set(target_point_ids.get(case["label"], []))

    sparse_vecs = list(bm25_model.query_embed(claim))
    if sparse_vecs:
        sv = sparse_vecs[0]
        indices = sv.indices.tolist()
        values = sv.values.tolist()

        bm25_results = c.query_points(
            collection_name=bm25_col,
            query=models.SparseVector(indices=indices, values=values),
            using="bm25",
            limit=100,
            with_payload=["ref_id", "rt_id", "section"],
        )

        bm25_found_rank = None
        for rank, pt in enumerate(bm25_results.points, 1):
            if pt.id in target_ids:
                ref = pt.payload.get("ref_id", "?")[:50]
                sec = pt.payload.get("section", "?")[:50]
                print(f"  BM25 rank: #{rank} | score={pt.score:.4f} | ref={ref} | section={sec}")
                if bm25_found_rank is None:
                    bm25_found_rank = rank

        if bm25_found_rank is None:
            print(f"  BM25 rank: NOT IN TOP 100!")

        print(f"  BM25 top 3:")
        for i, pt in enumerate(bm25_results.points[:3], 1):
            ref = pt.payload.get("ref_id", "?")[:45]
            print(f"    #{i}: score={pt.score:.4f} | {ref} | {pt.payload.get('section', '?')[:50]}")

print("\n\nDONE")
