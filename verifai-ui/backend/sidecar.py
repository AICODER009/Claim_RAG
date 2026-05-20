"""
VerifAI FastAPI Sidecar
Wraps the existing Python substantiation pipeline as an HTTP API.
Loads MedCPT + BM25 once on startup — no cold-start per request.
"""
from __future__ import annotations

import logging
import os
import sys
import time
import types
import importlib
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Path setup ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent  # verifai-ui/backend/../../ = verifai-ui/
PIPELINE_ROOT = ROOT.parent          # new_pipeline/new_pipeline/
PROJECT_ROOT = PIPELINE_ROOT.parent  # new_pipeline/ (outer)
sys.path.insert(0, str(PROJECT_ROOT))  # so 'from new_pipeline.config' works
sys.path.insert(0, str(PIPELINE_ROOT))



from dotenv import load_dotenv
load_dotenv(PIPELINE_ROOT / ".env", override=True)

_HF_CACHE = str(Path.home() / ".cache" / "huggingface")
os.environ.setdefault("HF_HOME", _HF_CACHE)
os.environ.setdefault("TRANSFORMERS_CACHE", _HF_CACHE)

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
logger = logging.getLogger("verifai.sidecar")

# ── Global pipeline state ────────────────────────────────────────────────────
_state: dict = {}


def _load_pipeline():
    """Load all heavy models once on startup."""
    import torch
    from transformers import AutoTokenizer, AutoModel
    from fastembed.sparse.bm25 import Bm25
    from qdrant_client import QdrantClient

    from new_pipeline.config import load_config
    from new_pipeline.retrieval.hybrid_retriever import HybridRetriever
    from new_pipeline.retrieval.mapping_matrix import MappingMatrix
    from new_pipeline.retrieval.claim_rewriter import ClaimRewriter
    from new_pipeline.evaluation.substantiation_judge import SubstantiationJudge
    from new_pipeline.schemas import ClaimClassification, PICOTComponents

    cfg = load_config()

    logger.info("Loading MedCPT Query Encoder…")
    q_tok = AutoTokenizer.from_pretrained("ncbi/MedCPT-Query-Encoder",
                                           cache_dir=_HF_CACHE)
    q_mod = AutoModel.from_pretrained("ncbi/MedCPT-Query-Encoder",
                                       cache_dir=_HF_CACHE, low_cpu_mem_usage=True)
    q_mod.eval()
    q_mod.half()

    logger.info("Loading BM25…")
    bm25 = Bm25(model_name="Qdrant/bm25", cache_dir=_HF_CACHE)

    logger.info("Connecting to Qdrant…")
    qdrant = QdrantClient(url=cfg.qdrant.url, api_key=cfg.qdrant.api_key, timeout=30)
    matrix = MappingMatrix(cfg.claim_mapping_path)

    rewriter = ClaimRewriter(
        provider="openai",
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        api_key=cfg.llm.openai_api_key,
    )
    retriever = HybridRetriever(
        qdrant_client=qdrant,
        collection_name=cfg.qdrant.collection_name,
        mapping_matrix=matrix,
        bm25_model=bm25,
    )
    judge = SubstantiationJudge(
        api_key=cfg.llm.anthropic_api_key,
        model=os.getenv("JUDGE_MODEL", "claude-sonnet-4-6"),
        requirements_path=PIPELINE_ROOT / "categorization" / "Claim_Substantiation_Requirements_v1_1.md",
    )

    _state.update({
        "cfg": cfg, "q_tok": q_tok, "q_mod": q_mod, "bm25": bm25,
        "retriever": retriever, "rewriter": rewriter, "judge": judge,
        "ClaimClassification": ClaimClassification, "PICOTComponents": PICOTComponents,
        "torch": torch,
    })
    logger.info("Pipeline ready ✓")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_pipeline()
    yield
    logger.info("Sidecar shutting down")


app = FastAPI(title="VerifAI Sidecar", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"],
                   allow_methods=["*"], allow_headers=["*"])


# ── Request / Response models ────────────────────────────────────────────────
class RunClaimRequest(BaseModel):
    claim_text: str
    ct_id: str
    top_k: int = 20


class PassageOut(BaseModel):
    ref_id: str
    rt_id: Optional[str] = None
    tier: Optional[str] = None
    section: Optional[str] = None
    segment_type: Optional[str] = None
    text: str
    numeric_tokens: list = []
    score: Optional[float] = None


class RunClaimResponse(BaseModel):
    verdict: str
    coverage_score: float
    assessment: str
    sub_assertions: list
    passages: list
    rewritten_query: str
    run_time_s: float
    model_judge: str
    model_rewriter: str


# ── Endpoints ────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "models_loaded": bool(_state)}


@app.get("/corpus/sources")
def corpus_sources():
    """List all unique ref_ids and their tier from Qdrant (sampled)."""
    try:
        cfg = _state["cfg"]
        from qdrant_client import QdrantClient
        client = QdrantClient(url=cfg.qdrant.url, api_key=cfg.qdrant.api_key, timeout=30)
        results, _ = client.scroll(cfg.qdrant.collection_name, limit=5000,
                                    with_payload=True, with_vectors=False)
        seen: dict = {}
        for r in results:
            rid = r.payload.get("ref_id", "unknown")
            if rid not in seen:
                seen[rid] = {"ref_id": rid,
                              "tier": r.payload.get("tier", "?"),
                              "ref_type": r.payload.get("reference_type_name", ""),
                              "chunk_count": 0}
            seen[rid]["chunk_count"] += 1
        return sorted(seen.values(), key=lambda x: x["ref_id"])
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/run_claim", response_model=RunClaimResponse)
def run_claim(req: RunClaimRequest):
    if not _state:
        raise HTTPException(503, "Pipeline not loaded yet")

    t0 = time.time()
    torch = _state["torch"]
    q_tok = _state["q_tok"]
    q_mod = _state["q_mod"]
    retriever = _state["retriever"]
    rewriter = _state["rewriter"]
    judge = _state["judge"]
    ClaimClassification = _state["ClaimClassification"]
    PICOTComponents = _state["PICOTComponents"]

    # 1. Rewrite claim → question
    query = rewriter.rewrite(req.claim_text)

    # 2. Encode with MedCPT
    with torch.no_grad():
        enc = q_tok(query, max_length=64, truncation=True,
                     padding=True, return_tensors="pt")
        qv = q_mod(**enc).last_hidden_state[:, 0, :][0].float().tolist()

    # 3. Retrieve
    passages = retriever.search(
        query_vector=qv,
        query_text=query,
        bm25_query_text=req.claim_text,
        ct_id=req.ct_id,
        final_top_k=req.top_k + 10,
    )

    # 4. Judge
    raw = judge.evaluate(
        claim_text=req.claim_text,
        classification=ClaimClassification(
            ct_id=req.ct_id,
            claim_type_name=req.ct_id,
            confidence=0.9,
        ),
        picot=PICOTComponents(),
        evidence_passages=passages[: req.top_k],
    )

    cov = raw.get("coverage_score", 0.0)
    if isinstance(cov, str):
        try:
            cov = float(cov.strip("%"))
        except Exception:
            cov = 0.0
    cov = float(cov)
    # Normalize: if > 1, assume it's 0-100 scale
    if cov > 1.0:
        cov = cov / 100.0
    cov = max(0.0, min(1.0, cov))

    if cov >= 0.70:
        verdict = "PASS"
    elif cov >= 0.40:
        verdict = "SOFT_FLAG"
    else:
        verdict = "BLOCK"

    # Serialize passages for JSON
    passages_out = []
    for p in passages[: req.top_k]:
        raw_tokens = p.get("numeric_tokens", [])
        # numeric_tokens from Qdrant may be dicts like {"value": "6", "context": "..."} — flatten to strings
        clean_tokens = []
        for t in (raw_tokens or []):
            if isinstance(t, dict):
                clean_tokens.append(str(t.get("value", t.get("context", str(t)))))
            else:
                clean_tokens.append(str(t))
        doc_meta = p.get("doc_metadata") or {}
        authors = doc_meta.get("authors") or []
        author_str = authors[0] if isinstance(authors, list) and authors else str(doc_meta.get("author", "") or "")
        passages_out.append({
            "ref_id": p.get("ref_id", ""),
            "ref_title": str(p.get("ref_title", "") or ""),   # Real paper title from GPT extraction
            "page": p.get("page"),                              # Page number (1-indexed)
            "rt_id": p.get("rt_id"),
            "tier": p.get("tier"),
            "section": p.get("section"),
            "segment_type": p.get("segment_type"),
            "text": p.get("text", ""),
            "numeric_tokens": clean_tokens,
            "score": p.get("final_score"),
            # Full bibliographic metadata
            "doc_title": str(doc_meta.get("title", "") or ""),
            "doc_author": author_str,
            "doc_year": str(doc_meta.get("year", "") or ""),
            "doc_journal": str(doc_meta.get("journal", "") or ""),
            "doc_doi": str(doc_meta.get("doi", "") or ""),
        })

    return RunClaimResponse(
        verdict=verdict,
        coverage_score=cov,
        assessment=raw.get("overall_assessment", ""),
        sub_assertions=raw.get("sub_assertions", []),
        passages=passages_out,
        rewritten_query=query,
        run_time_s=round(time.time() - t0, 1),
        model_judge=os.getenv("JUDGE_MODEL", "claude-sonnet-4-6"),
        model_rewriter=os.getenv("OPENAI_MODEL", "gpt-4o"),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("sidecar:app", host="127.0.0.1", port=8001, reload=False)
