"""Show a sample Qdrant point payload."""
import os, sys, json
sys.path.insert(0, r"D:\pip_libs")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\.env"))
from qdrant_client import QdrantClient

url = os.getenv("QDRANT_URL", "").strip('"')
key = os.getenv("QDRANT_API_KEY", "").strip('"')
client = QdrantClient(url=url, api_key=key, timeout=30)

# Get collection info
info = client.get_collection("verifai_mlr")
print(f"Collection: verifai_mlr")
print(f"Points: {info.points_count}")
print(f"Vector dim: {info.config.params.vectors.size}")
print(f"Distance: {info.config.params.vectors.distance}")

# Get one sample point
points = client.scroll(
    collection_name="verifai_mlr",
    limit=1,
    with_payload=True,
    with_vectors=True,
)[0]

p = points[0]
payload = p.payload
vec = p.vector[:5]  # just first 5 dims

print(f"\n{'='*60}")
print(f"SAMPLE POINT")
print(f"{'='*60}")
print(f"ID: {p.id}")
print(f"Vector (first 5): {vec}")
print(f"\nPayload fields:")
for k, v in payload.items():
    if k == "text":
        print(f"  text: '{v[:120]}...'")
    elif k == "source_table_html":
        print(f"  source_table_html: '{v[:60]}...' ({len(v)} chars)" if v else f"  source_table_html: ''")
    elif k == "doc_references":
        print(f"  doc_references: [{len(v)} entries]")
        if v:
            print(f"    [0]: {json.dumps(v[0], ensure_ascii=False)[:100]}")
    elif k == "doc_metadata":
        print(f"  doc_metadata: {json.dumps(v, ensure_ascii=False)[:150]}")
    elif k == "numeric_tokens":
        print(f"  numeric_tokens: {v[:5]}{'...' if len(v) > 5 else ''}")
    else:
        print(f"  {k}: {v}")
