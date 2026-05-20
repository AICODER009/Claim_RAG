"""Check if 77% can be directly calculated from Mendoza 2023 data in the corpus."""
import sys, os
sys.path.insert(0, "D:\\pip_packages")
from qdrant_client import QdrantClient, models
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env", override=True)
client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"), timeout=30)

print("=" * 70)
print("Searching Mendoza 2023 chunks about medication data")
print("=" * 70)

# Search for medication-related chunks from Mendoza
results = client.scroll(
    collection_name="verifai_mlr",
    scroll_filter=models.Filter(must=[
        models.FieldCondition(key="text", match=models.MatchText(text="mendoza")),
    ]),
    limit=50, with_payload=True,
)
# That might not work if Mendoza is in ref_id only. Try another approach:
# Search for unique text patterns from Mendoza 2023
results2 = client.scroll(
    collection_name="verifai_mlr",
    scroll_filter=models.Filter(must=[
        models.FieldCondition(key="text", match=models.MatchText(text="symptom satisfied")),
        models.FieldCondition(key="text", match=models.MatchText(text="dissatisfied")),
    ]),
    limit=20, with_payload=True,
)

print(f"\nChunks with 'symptom satisfied' + 'dissatisfied': {len(results2[0])}\n")
for i, p in enumerate(results2[0]):
    text = p.payload.get("text", "")
    ref = p.payload.get("ref_id", "?")[:40]
    section = p.payload.get("section", "?")[:50]
    print(f"--- Chunk {i+1} [{ref}] [{section}] ---")
    print(text[:600])
    print()

# Also search for the specific medication table data
print("\n" + "=" * 70)
print("Searching for 'current medications' + '190'")
print("=" * 70)
results3 = client.scroll(
    collection_name="verifai_mlr",
    scroll_filter=models.Filter(must=[
        models.FieldCondition(key="text", match=models.MatchText(text="medications")),
        models.FieldCondition(key="text", match=models.MatchText(text="190")),
    ]),
    limit=20, with_payload=True,
)
for i, p in enumerate(results3[0]):
    text = p.payload.get("text", "")
    ref = p.payload.get("ref_id", "?")[:40]
    print(f"--- Chunk {i+1} [{ref}] ---")
    print(text[:800])
    print()
