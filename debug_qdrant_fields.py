r"""
Debug script: inspect Qdrant payload fields to check if 'page' and 'ref_title'
are actually stored in the collection.
Run from: c:\Users\User\Downloads\new_pipeline\new_pipeline\
Usage: .venv\Scripts\python.exe debug_qdrant_fields.py
"""

from qdrant_client import QdrantClient

QDRANT_URL = "https://6bceb4fd-dd2e-40f5-8351-b58710be2501.us-east-1-1.aws.cloud.qdrant.io:6333"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6YTZhYjY1NDAtMTRhNi00Yjc4LTk2ZDQtNWM1NGQyYzY1YjMxIn0.SbPQAIfmi6acjS6a5kF2RPef8_f3u0RMrYFBe58uTyk"
COLLECTION = "verifai_mlr"

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=30)

print(f"\n{'='*60}")
print(f"Collection: {COLLECTION}")
print(f"{'='*60}\n")

# 1. Check collection info
info = client.get_collection(COLLECTION)
print(f"Status:        {info.status}")
print(f"Points count:  {getattr(info, 'points_count', 'n/a')}")
print()

# 2. Scroll a sample of 5 points and inspect ALL payload keys
print("── Sample payload keys (first 5 points) ──")
results, _ = client.scroll(
    collection_name=COLLECTION,
    limit=5,
    with_payload=True,
    with_vectors=False,
)

all_keys = set()
for i, point in enumerate(results):
    payload = point.payload or {}
    keys = set(payload.keys())
    all_keys |= keys
    print(f"\nPoint {i+1} (id={point.id}):")
    print(f"  Keys present: {sorted(keys)}")
    # Show specific fields we care about
    for field in ["page", "ref_title", "ref_id", "doc_title", "doc_author", "doc_year", "section", "text"]:
        val = payload.get(field)
        if val is not None:
            display = str(val)[:80] + ("…" if len(str(val)) > 80 else "")
            print(f"  {field:15s}: {display}")
        else:
            print(f"  {field:15s}: *** MISSING ***")

    # ── NEW: dump doc_metadata contents ──
    dm = payload.get("doc_metadata")
    if dm:
        print(f"  doc_metadata keys: {sorted(dm.keys()) if isinstance(dm, dict) else type(dm)}")
        if isinstance(dm, dict):
            for k, v in dm.items():
                display = str(v)[:80] + ("…" if len(str(v)) > 80 else "")
                print(f"    doc_metadata.{k:15s}: {display}")
    else:
        print(f"  doc_metadata   : *** MISSING ***")

print(f"\n── All unique payload keys across sample ──")
print(sorted(all_keys))

# 3. Check specifically for 'page' field — how many points have it?
print("\n── Checking 'page' field across 50 points ──")
results2, _ = client.scroll(
    collection_name=COLLECTION,
    limit=50,
    with_payload=["page", "ref_title", "ref_id"],
    with_vectors=False,
)

has_page = sum(1 for p in results2 if p.payload and p.payload.get("page") is not None)
has_ref_title = sum(1 for p in results2 if p.payload and p.payload.get("ref_title"))
print(f"  Points with 'page':      {has_page} / {len(results2)}")
print(f"  Points with 'ref_title': {has_ref_title} / {len(results2)}")

# 4. Show an example of a point that HAS page field (if any)
for p in results2:
    if p.payload and p.payload.get("page") is not None:
        print(f"\n  Example point WITH 'page':")
        print(f"    page      = {p.payload.get('page')}")
        print(f"    ref_title = {p.payload.get('ref_title')}")
        print(f"    ref_id    = {p.payload.get('ref_id')}")
        break
else:
    print("\n  *** NO points with 'page' field found in sample! ***")
    print("  → The 'page' field was never ingested into Qdrant.")
    print("  → You need to re-ingest documents with the page metadata field.")

print(f"\n{'='*60}")
print("CONCLUSION:")
if has_page == 0:
    print("  ✗ 'page' field is NOT in Qdrant — must re-ingest PDFs with page tracking")
else:
    print(f"  ✓ 'page' field exists in {has_page}/{len(results2)} sampled points")
if has_ref_title == 0:
    print("  ✗ 'ref_title' field is NOT in Qdrant — must re-ingest PDFs with title metadata")
else:
    print(f"  ✓ 'ref_title' field exists in {has_ref_title}/{len(results2)} sampled points")
print(f"{'='*60}\n")
