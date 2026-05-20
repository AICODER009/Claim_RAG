#!/usr/bin/env python3
"""
Quick smoke test — retrieval only, no LLM calls.
Checks that Allen_Lancet 32% infection chunk now appears in top 15 after brand-name auto-strip fix.
"""
import sys, os, types, importlib, logging
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

_ort = types.ModuleType("onnxruntime"); _ort.__spec__ = importlib.machinery.ModuleSpec("onnxruntime", None)
_ort.SessionOptions = type("x", (), {}); _ort.InferenceSession = type("x", (), {})
_ort.GraphOptimizationLevel = type("x", (), {"ORT_ENABLE_ALL": 99})
_c = types.ModuleType("onnxruntime.capi"); _c.__spec__ = importlib.machinery.ModuleSpec("onnxruntime.capi", None)
_p = types.ModuleType("onnxruntime.capi._pybind_state"); _p.__spec__ = importlib.machinery.ModuleSpec("onnxruntime.capi._pybind_state", None)
sys.modules["onnxruntime"] = _ort; sys.modules["onnxruntime.capi"] = _c; sys.modules["onnxruntime.capi._pybind_state"] = _p
sys.path.insert(0, r"D:\pip_packages")

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env", override=True)
os.environ["HF_HOME"] = r"D:\hf_cache"

from qdrant_client import QdrantClient
from new_pipeline.config import load_config
from new_pipeline.retrieval.hybrid_retriever import HybridRetriever
from new_pipeline.retrieval.mapping_matrix import MappingMatrix
from fastembed.sparse.bm25 import Bm25
from transformers import AutoTokenizer, AutoModel
import torch

cfg = load_config()
qdrant = QdrantClient(url=cfg.qdrant.url, api_key=cfg.qdrant.api_key, timeout=30)
matrix = MappingMatrix(cfg.claim_mapping_path)
q_tok = AutoTokenizer.from_pretrained("ncbi/MedCPT-Query-Encoder", cache_dir=r"D:\hf_cache")
q_mod = AutoModel.from_pretrained("ncbi/MedCPT-Query-Encoder", cache_dir=r"D:\hf_cache", low_cpu_mem_usage=True)
q_mod.eval(); q_mod.half()
bm25_model = Bm25(model_name="Qdrant/bm25", cache_dir=r"D:\hf_cache")
retriever = HybridRetriever(qdrant_client=qdrant, collection_name=cfg.qdrant.collection_name,
                            mapping_matrix=matrix, bm25_model=bm25_model)

def encode(text):
    with torch.no_grad():
        enc = q_tok(text, max_length=64, truncation=True, padding=True, return_tensors="pt")
        return q_mod(**enc).last_hidden_state[:, 0, :][0].float().tolist()

# Test all 3 CT-301 false-block claims (retrieval only — no LLM)
tests = [
    {"label": "#242", "claim": "In ADHERE Stage B, infections occurred in 32% of patients treated with VYVGART Hytrulo and 34% of placebo-treated patients.", "ct_id": "CT-301", "query": "What were the infection rates in VYVGART Hytrulo versus placebo groups in the ADHERE Stage B study?", "target": "Allen_Lancet", "want_top_k": 10},
    {"label": "#243", "claim": "The common infections were COVID-19 (17% VYVGART Hytrulo vs 13% placebo), nasopharyngitis (5% VYVGART Hytrulo vs 8% placebo).", "ct_id": "CT-301", "query": "What are the most common infections with VYVGART Hytrulo vs placebo in the ADHERE study?", "target": "Allen_Lancet", "want_top_k": 10},
    {"label": "#245", "claim": "Injection site reactions were bruising (5% VYVGART Hytrulo vs 1% placebo) and erythema (5% VYVGART Hytrulo and 0% placebo).", "ct_id": "CT-301", "query": "What are the rates of injection site reactions including bruising and erythema with VYVGART Hytrulo vs placebo?", "target": "Allen_Lancet", "want_top_k": 12},
]

print("="*70)
all_pass = True
for t in tests:
    qv = encode(t["query"])
    passages = retriever.search(query_vector=qv, query_text=t["query"],
                                bm25_query_text=t["claim"], ct_id=t["ct_id"], final_top_k=25)
    lancet_ranks = [i+1 for i, p in enumerate(passages)
                    if t["target"].lower() in p.get("ref_id","").lower()]
    passed = bool(lancet_ranks) and lancet_ranks[0] <= t["want_top_k"]
    icon = "✅" if passed else "❌"
    print(f"{icon} {t['label']} | Allen_Lancet ranks: {lancet_ranks[:5] or 'NOT FOUND'} | want top-{t['want_top_k']}")
    if not passed:
        all_pass = False
    # Show source diversity
    ref_counts = {}
    for p in passages[:15]:
        ref = p.get("ref_id","?")[:40]
        ref_counts[ref] = ref_counts.get(ref, 0) + 1
    for ref, cnt in sorted(ref_counts.items(), key=lambda x: -x[1])[:4]:
        print(f"   {cnt}x {ref}")
    print()

print("="*70)
print("RESULT:", "ALL RETRIEVAL CHECKS PASSED ✅" if all_pass else "SOME STILL FAILING ❌")
