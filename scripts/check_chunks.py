"""Quick diagnostic: search Qdrant for chunks containing 'freeze' from VYVGART PI."""
import sys, os
sys.path.insert(0, "D:\\pip_packages")
from qdrant_client import QdrantClient, models
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env", override=True)

cfg_url = os.getenv("QDRANT_URL") or os.getenv("QDRANT_CLOUD_URL")
cfg_key = os.getenv("QDRANT_API_KEY") or os.getenv("QDRANT_CLOUD_API_KEY")
client = QdrantClient(url=cfg_url, api_key=cfg_key, timeout=30)

# Search main collection for "freeze" in VYVGART docs
for collection in ["verifai_mlr", "verifai_mlr_bm25"]:
    print(f"\n=== Collection: {collection} ===")
    try:
        results = client.scroll(
            collection_name=collection,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(key="text", match=models.MatchText(text="freeze")),
                ]
            ),
            limit=20,
            with_payload=True,
        )
        points = results[0]
        print(f"Found {len(points)} chunks containing 'freeze'")
        for i, p in enumerate(points):
            ref = p.payload.get("ref_id", "?")
            section = p.payload.get("section", "?")
            text = p.payload.get("text", "")
            chars = len(text)
            # Check if it's VYVGART
            is_vyv = "vyvgart" in ref.lower() or "vyvgart" in text.lower()
            marker = "🎯 VYVGART" if is_vyv else ""
            print(f"\n[{i+1}] {marker} ref={ref[:50]}")
            print(f"    section: {section[:80]}")
            print(f"    chars: {chars}")
            # Find the freeze sentence
            for line in text.split("."):
                if "freeze" in line.lower() or "frozen" in line.lower():
                    print(f"    >>> {line.strip()[:120]}")
    except Exception as e:
        print(f"Error: {e}")

# Also search for "warm" in VYVGART
print(f"\n\n=== Searching for 'warm' in VYVGART ===")
try:
    results = client.scroll(
        collection_name="verifai_mlr",
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(key="text", match=models.MatchText(text="warm")),
            ]
        ),
        limit=30,
        with_payload=True,
    )
    points = results[0]
    vyv_warm = [p for p in points if "vyvgart" in p.payload.get("ref_id", "").lower()]
    print(f"Found {len(vyv_warm)} VYVGART chunks containing 'warm'")
    for i, p in enumerate(vyv_warm):
        section = p.payload.get("section", "?")
        text = p.payload.get("text", "")
        print(f"\n[{i+1}] section: {section[:80]}")
        print(f"    chars: {len(text)}")
        for line in text.split("."):
            if "warm" in line.lower():
                print(f"    >>> {line.strip()[:150]}")
except Exception as e:
    print(f"Error: {e}")

# Search for "discard" + "share" in VYVGART
for term in ["discard", "share"]:
    print(f"\n\n=== Searching for '{term}' in VYVGART ===")
    try:
        results = client.scroll(
            collection_name="verifai_mlr",
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(key="text", match=models.MatchText(text=term)),
                ]
            ),
            limit=30,
            with_payload=True,
        )
        points = results[0]
        vyv = [p for p in points if "vyvgart" in p.payload.get("ref_id", "").lower()]
        print(f"Found {len(vyv)} VYVGART chunks containing '{term}'")
        for i, p in enumerate(vyv):
            section = p.payload.get("section", "?")
            text = p.payload.get("text", "")
            print(f"\n[{i+1}] section: {section[:80]}")
            for line in text.split("."):
                if term in line.lower():
                    print(f"    >>> {line.strip()[:150]}")
    except Exception as e:
        print(f"Error: {e}")
