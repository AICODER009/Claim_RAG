#!/usr/bin/env python3
"""
Definitive pipeline trace — uses EXACT same API calls as hybrid_retriever.py
Checks Allen_Lancet_2024 rank at every retrieval step.
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

logging.basicConfig(level=logging.WARNING)
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env", override=True)
os.environ["HF_HOME"] = r"D:\hf_cache"

from qdrant_client import QdrantClient, models
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchText
from new_pipeline.config import load_config
from new_pipeline.retrieval.hybrid_retriever import extract_keywords
from transformers import AutoTokenizer, AutoModel
from fastembed.sparse.bm25 import Bm25
import torch, numpy as np

cfg = load_config()
qdrant = QdrantClient(url=cfg.qdrant.url, api_key=cfg.qdrant.api_key, timeout=30)
q_tok = AutoTokenizer.from_pretrained("ncbi/MedCPT-Query-Encoder", cache_dir=r"D:\hf_cache")
q_mod = AutoModel.from_pretrained("ncbi/MedCPT-Query-Encoder", cache_dir=r"D:\hf_cache", low_cpu_mem_usage=True)
q_mod.eval(); q_mod.half()
bm25_model = Bm25(model_name="Qdrant/bm25", cache_dir=r"D:\hf_cache")

DENSE_COL = cfg.qdrant.collection_name
BM25_COL  = DENSE_COL + "_bm25"
CLAIM = "In ADHERE Stage B, infections occurred in 32% of patients treated with VYVGART Hytrulo and 34% of placebo-treated patients."
QUERY = "What were the infection rates in VYVGART Hytrulo versus placebo groups in the ADHERE Stage B study?"
TARGET = "Allen_Lancet Neuro_2024"

def find_ranks(pts, target):
    """Return list of (1-based-rank, item) for all matches."""
    return [(i+1, p) for i, p in enumerate(pts) if target.lower() in p.get("ref_id","").lower()]

def ref_id(p):
    return p.get("ref_id","?")

def encode(text):
    with torch.no_grad():
        enc = q_tok(text, max_length=64, truncation=True, padding=True, return_tensors="pt")
        emb = q_mod(**enc).last_hidden_state[:, 0, :]
        return emb[0].float().tolist()

print("Models ready.\n")
print(f"CLAIM : {CLAIM}")
print(f"QUERY : {QUERY}")
print(f"TARGET: {TARGET}\n")
SEP = "="*70

# ==========================================================
# STEP 1: Dense search — exact same call as _dense_search()
# ==========================================================
print(SEP)
qv = encode(QUERY)
r1 = qdrant.query_points(collection_name=DENSE_COL, query=qv, limit=150, with_payload=True)
dense = [{"ref_id": pt.payload.get("ref_id",""), "rt_id": pt.payload.get("rt_id",""),
          "score": pt.score, "id": pt.id, "text": pt.payload.get("text","")[:100]}
         for pt in r1.points]
hits1 = find_ranks(dense, TARGET)
print(f"STEP 1 — Dense MedCPT top-150:  Allen_Lancet ranks = {[r for r,_ in hits1] or 'NOT IN TOP 150'}")
if hits1:
    for rank, h in hits1[:3]:
        print(f"  rank {rank:3d}: score={h['score']:.4f}  text: {h['text'][:110]}")
else:
    print(f"  *** TARGET NOT IN TOP 150 — semantic gap confirmed ***")
print(f"  Rank  1: [{dense[0]['rt_id']}] {ref_id(dense[0])[:50]}  score={dense[0]['score']:.4f}")
print(f"  Rank 10: [{dense[9]['rt_id']}] {ref_id(dense[9])[:50]}  score={dense[9]['score']:.4f}")
print(f"  Rank 50: [{dense[49]['rt_id']}] {ref_id(dense[49])[:50]}  score={dense[49]['score']:.4f}")

# ==========================================================
# STEP 2: BM25 search — exact same call as _bm25_search()
# ==========================================================
print()
print(SEP)
try:
    q_vec = list(bm25_model.query_embed(CLAIM))[0]
    r2 = qdrant.query_points(
        collection_name=BM25_COL,
        query=models.SparseVector(indices=q_vec.indices.tolist(), values=q_vec.values.tolist()),
        using="bm25",
        limit=100,
        with_payload=True,
    )
    bm25_pts = [{"ref_id": pt.payload.get("ref_id",""), "rt_id": pt.payload.get("rt_id",""),
                 "score": pt.score, "id": pt.id, "text": pt.payload.get("text","")[:100]}
                for pt in r2.points]
    hits2 = find_ranks(bm25_pts, TARGET)
    print(f"STEP 2 — BM25 fastembed top-100: Allen_Lancet ranks = {[r for r,_ in hits2] or 'NOT IN TOP 100'}")
    if hits2:
        for rank, h in hits2[:3]:
            print(f"  rank {rank:3d}: score={h['score']:.4f}  text: {h['text'][:110]}")
    else:
        print(f"  *** TARGET NOT IN BM25 TOP 100 ***")
    print(f"  Rank  1: [{bm25_pts[0]['rt_id']}] {ref_id(bm25_pts[0])[:50]}  score={bm25_pts[0]['score']:.4f}")
    print(f"  Rank 10: [{bm25_pts[9]['rt_id']}] {ref_id(bm25_pts[9])[:50]}  score={bm25_pts[9]['score']:.4f}")
except Exception as e:
    print(f"STEP 2 — BM25: FAILED: {e}")
    bm25_pts = []

# ==========================================================
# STEP 3: AND-match — replicate _and_match_search logic
# ==========================================================
print()
print(SEP)
NOISE = {"evidence","supports","support","supporting","claim","avoiding","recommendation",
         "approach","method","according","regarding","concerning","suggests",
         "patients","treated","treatment","study","clinical"}
kws_raw = extract_keywords(CLAIM, max_keywords=30)
specific_kws = [kw for kw in kws_raw if kw.lower() not in NOISE and len(kw) >= 3][:8]
print(f"STEP 3 — AND-match keywords: {specific_kws}")

# Try the AND filter
text_conds = [FieldCondition(key="text", match=MatchText(text=kw)) for kw in specific_kws]
try:
    r3 = qdrant.scroll(
        collection_name=DENSE_COL,
        scroll_filter=Filter(must=text_conds),
        limit=50, with_payload=True,
    )
    and_pts = [{"ref_id": pt.payload.get("ref_id",""), "rt_id": pt.payload.get("rt_id",""),
                "text": pt.payload.get("text","")[:100]} for pt in r3[0]]
    hits3 = find_ranks(and_pts, TARGET)
    print(f"  AND-match ({len(specific_kws)} kws): {len(and_pts)} results | Allen_Lancet = {[r for r,_ in hits3] or 'NOT FOUND'}")
    if and_pts:
        print(f"  Rank 1: [{and_pts[0]['rt_id']}] {ref_id(and_pts[0])[:55]}")
    # Relaxed: try 4 keywords
    if not hits3:
        text_conds4 = text_conds[:4]
        r3b = qdrant.scroll(
            collection_name=DENSE_COL,
            scroll_filter=Filter(must=text_conds4),
            limit=100, with_payload=True,
        )
        and_pts4 = [{"ref_id": pt.payload.get("ref_id",""), "rt_id": pt.payload.get("rt_id",""),
                     "text": pt.payload.get("text","")[:100]} for pt in r3b[0]]
        hits3b = find_ranks(and_pts4, TARGET)
        print(f"  Relaxed AND-match (4 kws): {len(and_pts4)} results | Allen_Lancet = {[r for r,_ in hits3b] or 'NOT FOUND'}")
        if hits3b:
            for rank, h in hits3b[:2]:
                print(f"  rank {rank}: text: {h['text'][:110]}")
except Exception as e:
    print(f"  AND-match FAILED: {e}")

# ==========================================================
# STEP 4: Direct payload check — does the chunk exist and what's in it?
# ==========================================================
print()
print(SEP)
lancet_all, _ = qdrant.scroll(
    collection_name=DENSE_COL,
    scroll_filter=Filter(must=[FieldCondition(key="ref_id", match=MatchValue(value=TARGET))]),
    limit=100, with_payload=True, with_vectors=False,
)
print(f"STEP 4 — Allen_Lancet in DENSE collection: {len(lancet_all)} total chunks")
inf32 = [c for c in lancet_all if "32" in c.payload.get("text","") and "infect" in c.payload.get("text","").lower()]
print(f"  Chunks with '32' + 'infect': {len(inf32)}")
for c in inf32:
    txt = c.payload.get("text","")
    kw_coverage = [kw for kw in specific_kws if kw.lower() in txt.lower()]
    print(f"  id={c.id}  section={c.payload.get('section','')[:50]}")
    print(f"  kw_coverage ({len(kw_coverage)}/{len(specific_kws)}): {kw_coverage}")
    print(f"  text: {txt[:300]}")
    print()

# ==========================================================
# STEP 5: Is Allen_Lancet in BM25 collection?
# ==========================================================
print(SEP)
try:
    lancet_bm25, _ = qdrant.scroll(
        collection_name=BM25_COL,
        scroll_filter=Filter(must=[FieldCondition(key="ref_id", match=MatchValue(value=TARGET))]),
        limit=100, with_payload=True, with_vectors=False,
    )
    print(f"STEP 5 — Allen_Lancet in BM25 collection: {len(lancet_bm25)} chunks")
    if not lancet_bm25:
        print("  *** CRITICAL: Allen_Lancet NOT IN BM25 COLLECTION — it was never indexed for BM25 ***")
    else:
        inf32_b = [c for c in lancet_bm25 if "32" in c.payload.get("text","")]
        print(f"  BM25 chunks with '32': {len(inf32_b)}")
        print(f"  Sample: {lancet_bm25[0].payload.get('text','')[:150]}")
except Exception as e:
    print(f"STEP 5 — BM25 check: {e}")

# ==========================================================
# STEP 6: Cosine sim of the infection chunk vs. our query
# ==========================================================
print()
print(SEP)
print("STEP 6 — Cosine similarity: infection chunk vs. query vector")
if inf32:
    chunk_id = inf32[0].id
    fetched = qdrant.retrieve(collection_name=DENSE_COL, ids=[chunk_id], with_vectors=True, with_payload=True)
    if fetched and fetched[0].vector:
        cv = np.array(fetched[0].vector)
        qv_np = np.array(qv)
        cos = float(np.dot(cv, qv_np) / (np.linalg.norm(cv) * np.linalg.norm(qv_np)))
        print(f"  cos_sim(query, 32%_chunk) = {cos:.4f}")
        print(f"  dense rank-1 score         = {dense[0]['score']:.4f}")
        print(f"  dense rank-10 score        = {dense[9]['score']:.4f}")
        print(f"  dense rank-50 score        = {dense[49]['score']:.4f}")
        rank_est = next((i+1 for i, d in enumerate(dense) if d['score'] <= cos), ">150")
        print(f"  → Expected dense rank based on score: ~{rank_est}")
        # Also try embedding the CLAIM text (not the rewritten query)
        qv2 = encode(CLAIM)
        qv2_np = np.array(qv2)
        cos2 = float(np.dot(cv, qv2_np) / (np.linalg.norm(cv) * np.linalg.norm(qv2_np)))
        print(f"  cos_sim(RAW CLAIM, 32%_chunk) = {cos2:.4f}  (claim text, not rewritten)")
    else:
        print("  Could not fetch vector")
else:
    print("  No infection chunk found in dense collection")

print()
print(SEP)
print("DIAGNOSIS COMPLETE")
print()
print("ROOT CAUSE SUMMARY:")
if not hits1 or hits1[0][0] > 50:
    print("  ❌ DENSE: Allen_Lancet infection chunk ranks LOW — semantic embedding mismatch")
if not hits2 or hits2[0][0] > 50:
    print("  ❌ BM25:  Allen_Lancet infection chunk ranks LOW or missing")
if not inf32:
    print("  ❌ CORPUS: Infection 32% data NOT in Qdrant at all — ingestion gap")
