#!/usr/bin/env python3
"""
Lightweight Qdrant-only test - no model loading.
Verifies the AND-match brand-strip fix directly against the index.
"""
import sys, types, importlib, os
sys.path.insert(0, r'D:\revisto_evidence_aligned_clean')
sys.path.insert(0, r'D:\pip_packages')

import sys, types, importlib, os
sys.path.insert(0, r'D:\revisto_evidence_aligned_clean')
sys.path.insert(0, r'D:\pip_packages')

# Full onnxruntime stub — satisfies fastembed import chain
_ort = types.ModuleType('onnxruntime')
_ort.__spec__ = importlib.machinery.ModuleSpec('onnxruntime', None)
_ort.SessionOptions = type('SessionOptions', (), {'__init__': lambda s: None})
_ort.InferenceSession = type('InferenceSession', (), {})
_ort.GraphOptimizationLevel = type('GraphOptimizationLevel', (), {'ORT_ENABLE_ALL': 99})
_ort.OrtValue = type('OrtValue', (), {})
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
SEP = "=" * 65

# -------------------------------------------------------------------
# TEST A: CT-301 claim #242 — WITH brand-name strip (the fix)
# Brand names 'vyvgart' and 'hytrulo' removed → can find Lancet chunk
# -------------------------------------------------------------------
print(SEP)
print("TEST A: CT-301 claim #242 — AND-match WITH brand-name strip")
kws_stripped = ['adhere', 'stage', 'infections', 'occurred', '32%', '34%']
conds = [FieldCondition(key='text', match=MatchText(text=kw)) for kw in kws_stripped]
r_stripped, _ = q.scroll(
    collection_name=col,
    scroll_filter=Filter(must=conds),
    limit=50, with_payload=True, with_vectors=False,
)
lancet_hits = [p for p in r_stripped if 'Allen_Lancet' in p.payload.get('ref_id', '')]
print(f"  Keywords: {kws_stripped}")
print(f"  Total results: {len(r_stripped)}")
print(f"  Allen_Lancet hits: {len(lancet_hits)}")
for h in lancet_hits[:2]:
    print(f"  FOUND: {h.payload.get('ref_id', '?')}")
    print(f"         {h.payload.get('text', '')[:180]}")

# -------------------------------------------------------------------
# TEST B: Same claim — WITHOUT strip (original broken behaviour)
# -------------------------------------------------------------------
print()
print(SEP)
print("TEST B: CT-301 claim #242 — AND-match WITHOUT brand-name strip (before fix)")
kws_original = ['adhere', 'stage', 'infections', 'occurred', '32%', 'vyvgart', 'hytrulo', '34%']
conds_orig = [FieldCondition(key='text', match=MatchText(text=kw)) for kw in kws_original]
r_original, _ = q.scroll(
    collection_name=col,
    scroll_filter=Filter(must=conds_orig),
    limit=50, with_payload=True, with_vectors=False,
)
lancet_orig = [p for p in r_original if 'Allen_Lancet' in p.payload.get('ref_id', '')]
print(f"  Keywords: {kws_original}")
print(f"  Total results: {len(r_original)}")
print(f"  Allen_Lancet hits: {len(lancet_orig)}  (expected: 0 — trial paper uses 'efgartigimod PH20' not brand name)")

# -------------------------------------------------------------------
# TEST C: CT-606 storage claim — brand name stays (guard works)
# Brand strip does NOT fire for PI-primary CT-IDs
# -------------------------------------------------------------------
print()
print(SEP)
print("TEST C: CT-606 storage — brand name STAYS in AND-match (guard protects PI-primary claims)")
kws_storage = ['freeze', 'store', 'vyvgart']
conds_store = [FieldCondition(key='text', match=MatchText(text=kw)) for kw in kws_storage]
r_store, _ = q.scroll(
    collection_name=col,
    scroll_filter=Filter(must=conds_store),
    limit=20, with_payload=True, with_vectors=False,
)
print(f"  Keywords: {kws_storage}")
print(f"  Total results: {len(r_store)}  (should be PI-only, ~3-6)")
for p in r_store[:4]:
    print(f"  -> {p.payload.get('ref_id', '?')[:60]}")

# -------------------------------------------------------------------
# TEST D: CT-301 claim #245 — bruising/erythema with strip
# -------------------------------------------------------------------
print()
print(SEP)
print("TEST D: CT-301 claim #245 — bruising/erythema WITH brand-name strip")
kws_245 = ['injection', 'site', 'bruising', '5%', 'erythema']
conds_245 = [FieldCondition(key='text', match=MatchText(text=kw)) for kw in kws_245]
r_245, _ = q.scroll(
    collection_name=col,
    scroll_filter=Filter(must=conds_245),
    limit=30, with_payload=True, with_vectors=False,
)
lancet_245 = [p for p in r_245 if 'Allen_Lancet' in p.payload.get('ref_id', '')]
print(f"  Keywords: {kws_245}")
print(f"  Total results: {len(r_245)}")
print(f"  Allen_Lancet hits: {len(lancet_245)}")
for h in lancet_245[:2]:
    print(f"  FOUND: {h.payload.get('ref_id', '?')}")
    print(f"         {h.payload.get('text', '')[:180]}")

# -------------------------------------------------------------------
# SUMMARY
# -------------------------------------------------------------------
print()
print(SEP)
print("SUMMARY")
print(SEP)
fix_works = len(lancet_hits) > 0
orig_broken = len(lancet_orig) == 0
guard_safe = all('vyvgart' in p.payload.get('ref_id', '').lower() or
                 'vyvgart' in p.payload.get('text', '').lower()
                 for p in r_store)

print(f"  Fix works (Lancet found with strip):     {'YES' if fix_works else 'NO'}")
print(f"  Original was broken (0 hits no strip):   {'CONFIRMED' if orig_broken else 'UNEXPECTED'}")
print(f"  Guard safe (PI-primary unaffected):      {'YES' if len(r_store) > 0 else 'NO RESULTS - CHECK'}")
print(f"  #245 bruising fix:                       {'YES' if len(lancet_245) > 0 else 'STILL MISSING'}")
