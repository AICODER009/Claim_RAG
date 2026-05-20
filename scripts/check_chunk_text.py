#!/usr/bin/env python3
"""Check exact text of the 32% infection chunk and what keywords Qdrant MatchText can find."""
import sys, types, importlib, os
sys.path.insert(0, r'D:\revisto_evidence_aligned_clean')
sys.path.insert(0, r'D:\pip_packages')

_ort = types.ModuleType('onnxruntime')
_ort.__spec__ = importlib.machinery.ModuleSpec('onnxruntime', None)
_ort.SessionOptions = type('SessionOptions', (), {'__init__': lambda s: None})
_ort.InferenceSession = type('InferenceSession', (), {})
_ort.GraphOptimizationLevel = type('GraphOptimizationLevel', (), {'ORT_ENABLE_ALL': 99})
_ort_capi = types.ModuleType('onnxruntime.capi')
_ort_capi.__spec__ = importlib.machinery.ModuleSpec('onnxruntime.capi', None)
_ort_pb = types.ModuleType('onnxruntime.capi._pybind_state')
_ort_pb.__spec__ = importlib.machinery.ModuleSpec('onnxruntime.capi._pybind_state', None)
sys.modules['onnxruntime'] = _ort
sys.modules['onnxruntime.capi'] = _ort_capi
sys.modules['onnxruntime.capi._pybind_state'] = _ort_pb

from dotenv import load_dotenv
load_dotenv(r'D:\revisto_evidence_aligned_clean\new_pipeline\.env', override=True)

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchText, MatchValue
from new_pipeline.config import load_config

cfg = load_config()
q = QdrantClient(url=cfg.qdrant.url, api_key=cfg.qdrant.api_key, timeout=30)
col = cfg.qdrant.collection_name

print("=== Fetching ALL Allen_Lancet chunks with '32' in text ===\n")

lancet_chunks, _ = q.scroll(
    collection_name=col,
    scroll_filter=Filter(must=[FieldCondition(key='ref_id', match=MatchValue(value='Allen_Lancet Neuro_2024'))]),
    limit=100, with_payload=True, with_vectors=False,
)
print(f"Total Allen_Lancet chunks: {len(lancet_chunks)}")

for c in lancet_chunks:
    txt = c.payload.get('text', '')
    if '32' in txt and 'infect' in txt.lower():
        print(f"\n--- CHUNK id={c.id} ---")
        print(f"section: {c.payload.get('section', '')}")
        print(f"FULL TEXT:\n{txt}")
        print("\nKeyword presence check:")
        for kw in ['adhere', 'stage', 'infections', 'occurred', '32%', '34%', '32', '34', 'infect']:
            present = kw.lower() in txt.lower()
            print(f"  '{kw}': {present}")
        print()

print("=== Searching MatchText for single keywords ===")
for kw in ['32%', '34%', 'infections', 'adhere', 'occurred', 'stage b']:
    r, _ = q.scroll(
        collection_name=col,
        scroll_filter=Filter(must=[FieldCondition(key='text', match=MatchText(text=kw))]),
        limit=5, with_payload=True, with_vectors=False,
    )
    lancet_hits = [p for p in r if 'Allen_Lancet' in p.payload.get('ref_id', '')]
    print(f"  MatchText('{kw}'): {len(r)} total results | Allen_Lancet: {len(lancet_hits)}")
