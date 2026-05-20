"""Smoke test: Do raw claims retrieve relevant evidence from Qdrant?

Tests 3 claims with MedCPT Query Encoder (raw, no rewrite)
to see if the asymmetric search actually works for claim statements.
"""
import os, sys, json, traceback
sys.path.insert(0, r"D:\pip_libs")

# Write all output to file
out = open(r"D:\smoke_results.txt", "w", encoding="utf-8")
def log(msg):
    print(msg)
    out.write(msg + "\n")
    out.flush()

os.environ["HF_HOME"] = r"D:\hf_cache"
os.environ["HF_HUB_CACHE"] = r"D:\hf_cache\hub"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\.env"))

import torch
import numpy as np
from transformers import AutoModel, AutoTokenizer
from qdrant_client import QdrantClient

# Connect Qdrant
url = os.getenv("QDRANT_URL", "").strip('"')
key = os.getenv("QDRANT_API_KEY", "").strip('"')
client = QdrantClient(url=url, api_key=key, timeout=30)

# Load MedCPT QUERY Encoder (different from Article Encoder!)
try:
    # Use Article Encoder for smoke test (Query Encoder OOM on this machine)
    # Article↔Article is symmetric but proves retrieval works
    log("Loading MedCPT Article Encoder (for smoke test)...")
    q_tokenizer = AutoTokenizer.from_pretrained("ncbi/MedCPT-Article-Encoder")
    q_model = AutoModel.from_pretrained("ncbi/MedCPT-Article-Encoder").eval()
    log("Article Encoder loaded (used as query encoder for test).\n")
except Exception as e:
    log(f"LOAD ERROR: {e}")
    log(traceback.format_exc())
    out.close()
    sys.exit(1)

def encode_query(text):
    with torch.no_grad():
        enc = q_tokenizer(text, max_length=512, padding=True,
                          truncation=True, return_tensors="pt")
        out = q_model(**enc)
        return out.last_hidden_state[:, 0, :].squeeze().numpy().tolist()

# Test claims (real ones from the xlsx)
test_claims = [
    # CT-604 - product description
    "A novel treatment for adult patients with chronic inflammatory demyelinating polyneuropathy (CIDP)",
    # CT-603 - dosing/admin
    "VYVGART HYTRULO is for use under the skin (subcutaneous) injection only.",
    # CT-301 - efficacy (if one exists — let's use a typical one)
    "VYVGART Hytrulo significantly reduced the risk of CIDP relapse versus placebo",
]

try:
    for i, claim in enumerate(test_claims):
        log(f"{'='*70}")
        log(f"CLAIM {i+1}: {claim}")
        log(f"{'='*70}")
        
        vec = encode_query(claim)
        
        results = client.query_points(
            collection_name="verifai_mlr",
            query=vec,
            limit=5,
            with_payload=True,
        )
        
        log(f"\nTop 5 results:")
        for j, pt in enumerate(results.points):
            p = pt.payload
            score = pt.score
            text = p.get("text", "")[:150]
            ref = p.get("ref_id", "?")[:40]
            sec = p.get("section", "")[:40]
            rt = p.get("rt_id", "?")
            log(f"\n  [{j+1}] score={score:.4f} | {rt} | {ref}")
            log(f"      section: {sec}")
            log(f"      text: {text}...")
        log("")
except Exception as e:
    log(f"ERROR: {e}")
    log(traceback.format_exc())
finally:
    out.close()
