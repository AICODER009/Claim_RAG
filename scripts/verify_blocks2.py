#!/usr/bin/env python3
"""Check ONLY the freeze, discard, and novel claims."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "D:\\pip_packages")
sys.path.insert(0, "D:\\revisto_evidence_aligned_clean")
from dotenv import load_dotenv
load_dotenv("D:/revisto_evidence_aligned_clean/new_pipeline/.env", override=True)
from qdrant_client import QdrantClient, models
from new_pipeline.config import load_config

cfg = load_config()
c = QdrantClient(url=cfg.qdrant.url, api_key=cfg.qdrant.api_key, timeout=30)
col = cfg.qdrant.collection_name

# Focus on the KEY questions
SEARCHES = [
    ("BLOCK #10: 'Do not freeze' - is it in VYVGART PI?", "Do not freeze"),
    ("BLOCK #10: 'freeze' anywhere?", "freeze"),
    ("BLOCK #5: 'novel'", "novel"),
    ("BLOCK #21: 'Discard' in VYVGART PI?", "Discard"),
    ("BLOCK #2/#50: 'inject into a vein'", "inject into a vein"),
]

for label, term in SEARCHES:
    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"{'='*70}")
    res = c.scroll(
        collection_name=col,
        scroll_filter=models.Filter(
            must=[models.FieldCondition(key="text", match=models.MatchText(text=term))]
        ),
        limit=10,
        with_payload=["text", "ref_id", "rt_id"],
    )
    pts = res[0]
    if not pts:
        print(f"  NO RESULTS for '{term}'")
        continue
    print(f"  {len(pts)} hits for '{term}':")
    for pt in pts:
        ref = (pt.payload.get("ref_id") or "?")[:55]
        rt = pt.payload.get("rt_id") or "?"
        txt = pt.payload.get("text", "")
        for line in txt.split("\n"):
            if term.lower() in line.lower():
                print(f"    rt={rt} | {ref}")
                print(f"      >> \"{line.strip()[:140]}\"")
                break
        else:
            print(f"    rt={rt} | {ref} | (in chunk, no single line match)")

print("\nDONE")
