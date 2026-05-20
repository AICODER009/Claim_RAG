#!/usr/bin/env python3
"""
Run 4 blocked claims through full pipeline (rewriter + retriever + judge).
Uses GPT-5.2 for rewriting, Claude sonnet-4-6 for judging.
"""
import sys, os, types, importlib, time, logging
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"D:\revisto_evidence_aligned_clean")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, r"D:\pip_packages")

# ── onnxruntime stub ──────────────────────────────────────────────
_ort = types.ModuleType("onnxruntime")
_ort.__spec__ = importlib.machinery.ModuleSpec("onnxruntime", None)
_ort.SessionOptions = type("SessionOptions", (), {"__init__": lambda s: None,
    "graph_optimization_level": None})
_ort.InferenceSession = type("InferenceSession", (), {})
_ort.GraphOptimizationLevel = type("GraphOptimizationLevel", (), {"ORT_ENABLE_ALL": 99})
_ort.OrtValue = type("OrtValue", (), {})
_ort_c = types.ModuleType("onnxruntime.capi")
_ort_c.__spec__ = importlib.machinery.ModuleSpec("onnxruntime.capi", None)
_ort_p = types.ModuleType("onnxruntime.capi._pybind_state")
_ort_p.__spec__ = importlib.machinery.ModuleSpec("onnxruntime.capi._pybind_state", None)
sys.modules.update({"onnxruntime": _ort,
                    "onnxruntime.capi": _ort_c,
                    "onnxruntime.capi._pybind_state": _ort_p})

# ── env ───────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv(ROOT / "new_pipeline" / ".env", override=True)
os.environ["HF_HOME"] = r"D:\hf_cache"
os.environ["TRANSFORMERS_CACHE"] = r"D:\hf_cache"

logging.basicConfig(level=logging.WARNING)
logging.getLogger("new_pipeline.retrieval.hybrid_retriever").setLevel(logging.INFO)

# ── imports ───────────────────────────────────────────────────────
print("Loading models...", flush=True)
from qdrant_client import QdrantClient
from new_pipeline.config import load_config
from new_pipeline.retrieval.hybrid_retriever import HybridRetriever
from new_pipeline.retrieval.mapping_matrix import MappingMatrix
from new_pipeline.retrieval.claim_rewriter import ClaimRewriter
from new_pipeline.evaluation.substantiation_judge import SubstantiationJudge
from new_pipeline.schemas import ClaimClassification, PICOTComponents
from transformers import AutoTokenizer, AutoModel
from fastembed.sparse.bm25 import Bm25
import torch

cfg = load_config()
qdrant = QdrantClient(url=cfg.qdrant.url, api_key=cfg.qdrant.api_key, timeout=30)
matrix = MappingMatrix(cfg.claim_mapping_path)
q_tok = AutoTokenizer.from_pretrained("ncbi/MedCPT-Query-Encoder", cache_dir=r"D:\hf_cache")
q_mod = AutoModel.from_pretrained("ncbi/MedCPT-Query-Encoder", cache_dir=r"D:\hf_cache",
                                   low_cpu_mem_usage=True)
q_mod.eval(); q_mod.half()
bm25_model = Bm25(model_name="Qdrant/bm25", cache_dir=r"D:\hf_cache")

rewriter = ClaimRewriter(
    provider="openai",
    model=os.getenv("OPENAI_MODEL", "gpt-4o"),
    api_key=cfg.llm.openai_api_key,
)
judge = SubstantiationJudge(
    api_key=cfg.llm.anthropic_api_key,
    model=cfg.llm.judge_model,
    requirements_path=cfg.substantiation_requirements_path,
)
retriever = HybridRetriever(
    qdrant_client=qdrant,
    collection_name=cfg.qdrant.collection_name,
    mapping_matrix=matrix,
    bm25_model=bm25_model,
)
print("Models ready.\n", flush=True)

def encode(text):
    with torch.no_grad():
        enc = q_tok(text, max_length=64, truncation=True, padding=True, return_tensors="pt")
        return q_mod(**enc).last_hidden_state[:, 0, :][0].float().tolist()

# ── 4 previously false-blocked claims ────────────────────────────
CLAIMS = [
    {
        "label": "#242",
        "claim": "In ADHERE Stage B, infections occurred in 32% of patients treated with "
                 "VYVGART Hytrulo and 34% of placebo-treated patients.",
        "ct_id": "CT-301",
        "expected": "PASS",
    },
    {
        "label": "#243",
        "claim": "The common infections were COVID-19 (17% VYVGART Hytrulo vs 13% placebo), "
                 "nasopharyngitis (5% VYVGART Hytrulo vs 8% placebo), URTI (2% VYVGART Hytrulo "
                 "vs 10% placebo), and pneumonia (1% VYVGART Hytrulo vs 4% placebo).",
        "ct_id": "CT-301",
        "expected": "PASS or SOFT_FLAG",
    },
    {
        "label": "#245",
        "claim": "Injection site reactions were bruising (5% VYVGART Hytrulo vs 1% placebo) "
                 "and erythema (5% VYVGART Hytrulo and 0% placebo).",
        "ct_id": "CT-301",
        "expected": "PASS or SOFT_FLAG",
    },
    {
        "label": "#267",
        "claim": "Lower scores = more disability",
        "ct_id": "CT-803",
        "expected": "PASS",
    },
]

SEP = "=" * 65
results = []

for tc in CLAIMS:
    t0 = time.time()
    print(SEP, flush=True)
    print(f"Claim {tc['label']} | CT-ID: {tc['ct_id']}", flush=True)
    print(f"Text: {tc['claim'][:100]}", flush=True)

    # Step 1: Rewrite
    try:
        query = rewriter.rewrite(tc["claim"])
    except Exception as e:
        query = tc["claim"]
        print(f"  Rewriter fallback: {e}", flush=True)
    print(f"  Query: {query[:90]}", flush=True)

    # Step 2: Retrieve
    qv = encode(query)
    passages = retriever.search(
        query_vector=qv,
        query_text=query,
        bm25_query_text=tc["claim"],
        ct_id=tc["ct_id"],
        final_top_k=25,
    )

    # Source diversity
    ref_counts = {}
    for p in passages[:15]:
        r = p.get("ref_id", "?")[:40]
        ref_counts[r] = ref_counts.get(r, 0) + 1
    print(f"  Top sources (top-15):", flush=True)
    for ref, cnt in sorted(ref_counts.items(), key=lambda x: -x[1])[:5]:
        print(f"    {cnt}x {ref}", flush=True)

    lancet_ranks = [i+1 for i, p in enumerate(passages)
                    if "allen_lancet" in p.get("ref_id", "").lower()]
    print(f"  Allen_Lancet ranks: {lancet_ranks[:5] or 'NOT FOUND'}", flush=True)

    # Step 3: Judge
    try:
        raw = judge.evaluate(
            claim_text=tc["claim"],
            classification=ClaimClassification(
                ct_id=tc["ct_id"], claim_type_name=tc["ct_id"], confidence=0.9
            ),
            picot=PICOTComponents(),
            evidence_passages=passages[:20],  # increased from 15 — key trial chunks rank 9-15
        )
        cov = raw.get("coverage_score", 0)
        if isinstance(cov, str):
            try: cov = float(cov.replace("%", ""))
            except: cov = 0
    except Exception as e:
        print(f"  Judge error: {e}", flush=True)
        cov = 0
        raw = {}

    verdict = "PASS" if cov >= 80 else "SOFT_FLAG" if cov >= 60 else "BLOCK"
    elapsed = time.time() - t0
    icon = "✅" if verdict == "PASS" else "⚠️" if verdict == "SOFT_FLAG" else "❌"
    print(f"  {icon} Verdict: {verdict} ({cov}%) | {elapsed:.0f}s", flush=True)
    assessment = raw.get("overall_assessment", "")
    if assessment:
        print(f"  Assessment: {assessment[:220]}", flush=True)

    results.append({
        "label": tc["label"], "verdict": verdict,
        "coverage": cov, "expected": tc["expected"],
        "fixed": verdict != "BLOCK",
    })

# ── Summary ───────────────────────────────────────────────────────
print(f"\n{SEP}", flush=True)
print("REGRESSION SUMMARY", flush=True)
print(SEP, flush=True)
all_fixed = True
for r in results:
    icon = "✅ FIXED  " if r["fixed"] else "❌ BLOCKED"
    print(f"  {icon}  {r['label']}  |  {r['verdict']} ({r['coverage']}%)  "
          f"|  expected: {r['expected']}", flush=True)
    if not r["fixed"]:
        all_fixed = False

print(flush=True)
if all_fixed:
    print("ALL 4 FALSE BLOCKS RESOLVED ✅", flush=True)
else:
    n_fixed = sum(1 for r in results if r["fixed"])
    print(f"{n_fixed}/4 fixed. Remaining need further investigation.", flush=True)
