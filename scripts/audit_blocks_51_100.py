"""Quick audit: verify the 2 blocked claims from batch 51-100."""
import sys, os
sys.path.insert(0, "D:\\pip_packages")
from qdrant_client import QdrantClient, models
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env", override=True)
client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"), timeout=30)
COLLECTION = "verifai_mlr"

print("=" * 70)
print("BLOCK #91: 'CIDP can have a variable clinical course,")
print("            with chronic progressive being the most common'")
print("=" * 70)
print("\n--- Searching for 'chronic progressive most common' ---")
results = client.scroll(
    collection_name=COLLECTION,
    scroll_filter=models.Filter(must=[
        models.FieldCondition(key="text", match=models.MatchText(text="chronic")),
        models.FieldCondition(key="text", match=models.MatchText(text="progressive")),
        models.FieldCondition(key="text", match=models.MatchText(text="common")),
    ]),
    limit=10, with_payload=True,
)
for p in results[0]:
    ref = p.payload.get("ref_id", "?")[:40]
    text = p.payload.get("text", "")[:200].replace("\n", " ")
    print(f"  [{ref}] {text}")

print("\n--- Searching for 'chronic relapsing most common' ---")
results2 = client.scroll(
    collection_name=COLLECTION,
    scroll_filter=models.Filter(must=[
        models.FieldCondition(key="text", match=models.MatchText(text="chronic")),
        models.FieldCondition(key="text", match=models.MatchText(text="relapsing")),
        models.FieldCondition(key="text", match=models.MatchText(text="common")),
    ]),
    limit=10, with_payload=True,
)
for p in results2[0]:
    ref = p.payload.get("ref_id", "?")[:40]
    text = p.payload.get("text", "")[:200].replace("\n", " ")
    print(f"  [{ref}] {text}")

print("\n--- Searching for 'two-thirds' or '66%' related to course type ---")
results3 = client.scroll(
    collection_name=COLLECTION,
    scroll_filter=models.Filter(must=[
        models.FieldCondition(key="text", match=models.MatchText(text="two-thirds")),
        models.FieldCondition(key="text", match=models.MatchText(text="relapsing")),
    ]),
    limit=5, with_payload=True,
)
for p in results3[0]:
    ref = p.payload.get("ref_id", "?")[:40]
    text = p.payload.get("text", "")[:250].replace("\n", " ")
    print(f"  [{ref}] {text}")

print("\n" + "=" * 70)
print("BLOCK #99: '77% of 190 patients who report being dissatisfied")
print("            with their symptom burden are on 1 or more treatments'")
print("=" * 70)
print("\n--- Searching for '77%' or '77' + 'dissatisfied' ---")
results4 = client.scroll(
    collection_name=COLLECTION,
    scroll_filter=models.Filter(must=[
        models.FieldCondition(key="text", match=models.MatchText(text="77")),
        models.FieldCondition(key="text", match=models.MatchText(text="dissatisfied")),
    ]),
    limit=10, with_payload=True,
)
print(f"  Found: {len(results4[0])} chunks")
for p in results4[0]:
    ref = p.payload.get("ref_id", "?")[:40]
    text = p.payload.get("text", "")[:250].replace("\n", " ")
    print(f"  [{ref}] {text}")

print("\n--- Searching for '190' + 'treatment' ---")
results5 = client.scroll(
    collection_name=COLLECTION,
    scroll_filter=models.Filter(must=[
        models.FieldCondition(key="text", match=models.MatchText(text="190")),
        models.FieldCondition(key="text", match=models.MatchText(text="treatment")),
    ]),
    limit=10, with_payload=True,
)
print(f"  Found: {len(results5[0])} chunks")
for p in results5[0]:
    ref = p.payload.get("ref_id", "?")[:40]
    text = p.payload.get("text", "")[:250].replace("\n", " ")
    print(f"  [{ref}] {text}")

print("\n--- Searching for '146' + '190' (77% = 146/190) ---")
results6 = client.scroll(
    collection_name=COLLECTION,
    scroll_filter=models.Filter(must=[
        models.FieldCondition(key="text", match=models.MatchText(text="146")),
        models.FieldCondition(key="text", match=models.MatchText(text="190")),
    ]),
    limit=10, with_payload=True,
)
print(f"  Found: {len(results6[0])} chunks")
for p in results6[0]:
    ref = p.payload.get("ref_id", "?")[:40]
    text = p.payload.get("text", "")[:300].replace("\n", " ")
    print(f"  [{ref}] {text}")
