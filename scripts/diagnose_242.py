"""
Diagnostic: print exact text the judge sees for claim #242.
Checks whether 35 (32%) appears in any of the 20 passages sent.
"""
import sys, os, types, importlib, logging
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"D:\revisto_evidence_aligned_clean")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, r"D:\pip_packages")

# onnxruntime stub
_ort = types.ModuleType("onnxruntime")
_ort.__spec__ = importlib.machinery.ModuleSpec("onnxruntime", None)
_ort.SessionOptions = type("SessionOptions", (), {"__init__": lambda s: None, "graph_optimization_level": None})
_ort.InferenceSession = type("InferenceSession", (), {})
_ort.GraphOptimizationLevel = type("GraphOptimizationLevel", (), {"ORT_ENABLE_ALL": 99})
_ort_c = types.ModuleType("onnxruntime.capi")
_ort_c.__spec__ = importlib.machinery.ModuleSpec("onnxruntime.capi", None)
_ort_p = types.ModuleType("onnxruntime.capi._pybind_state")
_ort_p.__spec__ = importlib.machinery.ModuleSpec("onnxruntime.capi._pybind_state", None)
sys.modules.update({"onnxruntime": _ort, "onnxruntime.capi": _ort_c, "onnxruntime.capi._pybind_state": _ort_p})

from dotenv import load_dotenv
load_dotenv(ROOT / "new_pipeline" / ".env", override=True)
os.environ["HF_HOME"] = r"D:\hf_cache"; os.environ["TRANSFORMERS_CACHE"] = r"D:\hf_cache"
logging.basicConfig(level=logging.WARNING)

from qdrant_client import QdrantClient
from new_pipeline.config import load_config
from new_pipeline.retrieval.hybrid_retriever import HybridRetriever
from new_pipeline.retrieval.mapping_matrix import MappingMatrix
from new_pipeline.retrieval.claim_rewriter import ClaimRewriter
from new_pipeline.prompts.judge_prompt import format_evidence_passages
from transformers import AutoTokenizer, AutoModel
from fastembed.sparse.bm25 import Bm25
import torch

print("Loading...", flush=True)
cfg = load_config()
qdrant = QdrantClient(url=cfg.qdrant.url, api_key=cfg.qdrant.api_key, timeout=30)
matrix = MappingMatrix(cfg.claim_mapping_path)
q_tok = AutoTokenizer.from_pretrained("ncbi/MedCPT-Query-Encoder", cache_dir=r"D:\hf_cache")
q_mod = AutoModel.from_pretrained("ncbi/MedCPT-Query-Encoder", cache_dir=r"D:\hf_cache", low_cpu_mem_usage=True)
q_mod.eval(); q_mod.half()
bm25_model = Bm25(model_name="Qdrant/bm25", cache_dir=r"D:\hf_cache")
rewriter = ClaimRewriter(provider="openai", model=os.getenv("OPENAI_MODEL","gpt-4o"), api_key=cfg.llm.openai_api_key)
retriever = HybridRetriever(qdrant_client=qdrant, collection_name=cfg.qdrant.collection_name,
                             mapping_matrix=matrix, bm25_model=bm25_model)
print("Ready.\n", flush=True)

CLAIM = ("In ADHERE Stage B, infections occurred in 32% of patients treated with "
         "VYVGART Hytrulo and 34% of placebo-treated patients.")
CT_ID = "CT-301"

def encode(text):
    with torch.no_grad():
        enc = q_tok(text, max_length=64, truncation=True, padding=True, return_tensors="pt")
        return q_mod(**enc).last_hidden_state[:, 0, :][0].float().tolist()

query = rewriter.rewrite(CLAIM)
print(f"Query: {query}\n", flush=True)

qv = encode(query)
passages = retriever.search(query_vector=qv, query_text=query, bm25_query_text=CLAIM,
                             ct_id=CT_ID, final_top_k=25)

# Check each of top 20 for 32% and 34%
print("=== Checking top 20 passages for '32%' and '34%' ===", flush=True)
found_32 = False
found_34 = False
for i, p in enumerate(passages[:20], 1):
    text = p.get("text", "")
    ref = p.get("ref_id", "?")[:45]
    has_32 = "32%" in text or "32)" in text or "(32" in text
    has_34 = "34%" in text or "34)" in text or "(34" in text
    marker = ""
    if has_32 or has_34:
        marker = f"  ← {'32%' if has_32 else ''} {'34%' if has_34 else ''} FOUND"
        found_32 = found_32 or has_32
        found_34 = found_34 or has_34
    print(f"  P{i:02d} [{ref}]{marker}", flush=True)
    if marker:
        # Show the relevant sentence
        for sent in text.split('.'):
            if '32' in sent or '34' in sent:
                print(f"       >>> {sent.strip()[:200]}", flush=True)

print(flush=True)
if found_32 and found_34:
    print("✅ Both 32% and 34% ARE in the top-20 passages — judge should see them.", flush=True)
    print("   → Problem is judge recognition, not retrieval.", flush=True)
elif found_32 or found_34:
    print(f"⚠️  Only {'32%' if found_32 else '34%'} found. One is missing from top-20.", flush=True)
else:
    print("❌ Neither 32% nor 34% found in top-20 passages — RETRIEVAL GAP.", flush=True)
    print("   → The chunk exists in Qdrant but scores too low to reach top-20.", flush=True)

print("\n=== Judge-formatted text for Lancet passages ===", flush=True)
lancet = [p for p in passages[:20] if 'Allen_Lancet' in p.get('ref_id','')]
print(format_evidence_passages(lancet))
