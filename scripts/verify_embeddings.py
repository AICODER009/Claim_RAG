"""Verify embedding quality and validate the 3,000 skipped chunks."""
import sys, json, re
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

OUT = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\chunks_final")

total = 0
embedded = 0
skipped = 0
empty_vec_embeddable = 0
has_vec_non_embeddable = 0

# Vector quality checks
all_norms = []
all_dims = []
zero_vecs = 0
nan_vecs = 0
duplicate_vecs = set()

# Skipped breakdown
skip_by_type = {}

for jf in sorted(OUT.glob("*.chunks.json")):
    data = json.loads(jf.read_text(encoding="utf-8"))
    for c in data:
        total += 1
        vec = c.get("vector", [])
        seg = c["segment_type"]
        emb = c["embeddable"]

        if emb and len(vec) > 0:
            embedded += 1
            arr = np.array(vec, dtype=np.float32)
            all_dims.append(len(vec))
            norm = np.linalg.norm(arr)
            all_norms.append(norm)
            if norm < 1e-6:
                zero_vecs += 1
            if np.any(np.isnan(arr)):
                nan_vecs += 1
        elif emb and len(vec) == 0:
            empty_vec_embeddable += 1
        elif not emb and len(vec) > 0:
            has_vec_non_embeddable += 1
        elif not emb:
            skipped += 1
            skip_by_type[seg] = skip_by_type.get(seg, 0) + 1

print("=" * 60)
print("EMBEDDING VERIFICATION REPORT")
print("=" * 60)

print(f"\nTotal chunks: {total}")
print(f"Embedded (embeddable + has vector): {embedded}")
print(f"Skipped (non-embeddable, no vector): {skipped}")

print(f"\n--- INTEGRITY CHECKS ---")
print(f"Embeddable but MISSING vector: {empty_vec_embeddable}  {'PASS' if empty_vec_embeddable == 0 else 'FAIL'}")
print(f"Non-embeddable but HAS vector: {has_vec_non_embeddable}  {'PASS' if has_vec_non_embeddable == 0 else 'FAIL'}")

print(f"\n--- VECTOR QUALITY ---")
dims = set(all_dims)
print(f"Vector dimensions: {dims}  {'PASS (768)' if dims == {768} else 'FAIL'}")
print(f"Zero vectors (norm<1e-6): {zero_vecs}  {'PASS' if zero_vecs == 0 else 'FAIL'}")
print(f"NaN vectors: {nan_vecs}  {'PASS' if nan_vecs == 0 else 'FAIL'}")

norms = np.array(all_norms)
print(f"Norm range: [{norms.min():.4f}, {norms.max():.4f}]")
print(f"Norm mean: {norms.mean():.4f}, std: {norms.std():.4f}")

# Check for suspiciously uniform vectors
if len(norms) > 10:
    # Sample first 5 vectors to check they're different
    print(f"\n--- DIVERSITY CHECK (first 3 files) ---")

files = sorted(OUT.glob("*.chunks.json"))[:3]
for jf in files:
    data = json.loads(jf.read_text(encoding="utf-8"))
    vecs = [c["vector"] for c in data if c["embeddable"] and len(c["vector"]) > 0]
    if len(vecs) >= 2:
        v1 = np.array(vecs[0])
        v2 = np.array(vecs[1])
        cos_sim = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        print(f"  {jf.stem[:45]:45s} chunk0 vs chunk1 cosine: {cos_sim:.4f}")
        # Also check first vs last
        vl = np.array(vecs[-1])
        cos_sim_fl = np.dot(v1, vl) / (np.linalg.norm(v1) * np.linalg.norm(vl))
        print(f"  {'':45s} chunk0 vs chunkN cosine: {cos_sim_fl:.4f}")

print(f"\n--- WHY 3,000 WERE SKIPPED ---")
print(f"Skipped by segment_type:")
for seg, count in sorted(skip_by_type.items(), key=lambda x: -x[1]):
    print(f"  {seg:15s}: {count:5d}")

print(f"""
EXPLANATION:
  'reference' = bibliography entries (e.g. "1. Van den Bergh PY, et al...")
  'figure'    = figure captions and stripped image references

  These are INTENTIONALLY excluded from vector search because:
  1. References pollute retrieval — a search for "p=0.05" would match
     page ranges like "2021;28:3556-3583" in reference entries
  2. Figures are captions only (no visual data) — low retrieval value
  
  Both types are still STORED in JSON for audit — they just don't get
  embedded or uploaded to Qdrant. The LLM Judge can still access them
  via the full document payload if needed.
""")

# Final verdict
issues = empty_vec_embeddable + has_vec_non_embeddable + zero_vecs + nan_vecs
issues += 0 if dims == {768} else 1
print("=" * 60)
if issues == 0:
    print("VERDICT: ALL EMBEDDINGS VALID — Ready for Qdrant upload")
else:
    print(f"VERDICT: {issues} issues found")
print("=" * 60)
