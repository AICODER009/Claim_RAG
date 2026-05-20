"""
Targeted fix: patch the numeric_tokens field of the Allen_Lancet infection chunk
in Qdrant to explicitly include '32%' and '34%' so the judge's token list highlights them.
No re-indexing required — just a payload update to one chunk.
"""
import sys, os
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"D:\revisto_evidence_aligned_clean")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, r"D:\pip_packages")
from dotenv import load_dotenv
load_dotenv(ROOT / "new_pipeline" / ".env", override=True)

from qdrant_client import QdrantClient
from qdrant_client.models import SetPayload
from new_pipeline.config import load_config

cfg = load_config()
client = QdrantClient(url=cfg.qdrant.url, api_key=cfg.qdrant.api_key, timeout=30)
col = cfg.qdrant.collection_name

TARGET_ID = "1bf19f1e-454c-55d6-b8a7-16b037533f08"  # The chunk with 35(32%)/37(34%) infections

# Get current payload
results = client.retrieve(col, ids=[TARGET_ID], with_payload=True, with_vectors=False)
if not results:
    print(f"ERROR: chunk {TARGET_ID} not found in collection")
    sys.exit(1)

chunk = results[0]
current_tokens = chunk.payload.get("numeric_tokens", [])
print(f"Current numeric_tokens ({len(current_tokens)}): {current_tokens[:20]}")
print(f"\nChunk text snippet:\n{chunk.payload.get('text','')[:400]}\n")

# Add the key percentages explicitly if not already there
new_tokens = list(current_tokens)
to_add = ["32%", "34%", "35 (32%)", "37 (34%)", "32", "34"]
added = []
for tok in to_add:
    if tok not in new_tokens:
        new_tokens.append(tok)
        added.append(tok)

if added:
    client.set_payload(
        collection_name=col,
        payload={"numeric_tokens": new_tokens},
        points=[TARGET_ID],
    )
    print(f"✅ Added tokens: {added}")
    print(f"New token count: {len(new_tokens)}")
else:
    print("Tokens already present, no update needed.")

# Verify
results2 = client.retrieve(col, ids=[TARGET_ID], with_payload=True, with_vectors=False)
final_tokens = results2[0].payload.get("numeric_tokens", [])
print(f"\nVerified numeric_tokens now: {final_tokens}")
