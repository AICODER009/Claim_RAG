"""
Lightweight diagnostic for claim #242 — no model loading.
Directly queries Qdrant using the BM25 keyword filter for 32%/34%/infections
and prints what's in the indexed text.
"""
import sys, os
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"D:\revisto_evidence_aligned_clean")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, r"D:\pip_packages")

from dotenv import load_dotenv
load_dotenv(ROOT / "new_pipeline" / ".env", override=True)

from qdrant_client import QdrantClient
from new_pipeline.config import load_config
from new_pipeline.prompts.judge_prompt import format_evidence_passages

cfg = load_config()
client = QdrantClient(url=cfg.qdrant.url, api_key=cfg.qdrant.api_key, timeout=30)
col = cfg.qdrant.collection_name
print(f"Collection: {col}", flush=True)

# --- Scroll ALL Allen_Lancet chunks from Qdrant ---
all_lancet = []
offset = None
while True:
    batch, offset = client.scroll(col, limit=200, with_payload=True, with_vectors=False, offset=offset)
    all_lancet.extend([c for c in batch if 'Allen_Lancet' in str(c.payload.get('ref_id',''))])
    if offset is None:
        break

print(f"Total Allen_Lancet chunks in Qdrant: {len(all_lancet)}", flush=True)

# Check which ones contain the target data
print("\n=== Searching for '32%' / '34%' / 'infections' ===", flush=True)
for c in all_lancet:
    txt = c.payload.get('text', '')
    has_32 = '32%' in txt or '(32)' in txt or '32 (' in txt
    has_34 = '34%' in txt or '(34)' in txt or '34 (' in txt
    has_inf = 'infection' in txt.lower()
    if has_32 or has_34 or has_inf:
        flags = []
        if has_32: flags.append('32%')
        if has_34: flags.append('34%')
        if has_inf: flags.append('infection')
        print(f"\n  ID={c.id} flags={flags}", flush=True)
        print(f"  Text: {txt[:600]}", flush=True)

# Also check the chunks JSON file for comparison
print("\n\n=== From chunks_final JSON file ===", flush=True)
import json
jpath = ROOT / "new_pipeline/parsed/chunks_final/Allen_Lancet Neuro_2024.chunks.json"
with open(jpath, encoding='utf-8') as f:
    file_chunks = json.load(f)
print(f"Total chunks in file: {len(file_chunks)}", flush=True)

file_ids_with_32 = []
for i, c in enumerate(file_chunks):
    txt = c.get('text','')
    if ('32%' in txt or '35 (32' in txt) and 'infect' in txt.lower():
        print(f"\n  File chunk {i}: {txt[:500]}", flush=True)
        file_ids_with_32.append(i)

if not file_ids_with_32:
    print("  None found in file chunks!", flush=True)
