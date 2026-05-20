#!/usr/bin/env python3
"""Verify: what evidence actually exists for each blocked claim?"""
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

SEARCHES = [
    ("BLOCK #2: inject into vein or muscle", ["Do not administer intravenously", "intramuscular", "subcutaneous use only"]),
    ("BLOCK #5: novel treatment CIDP", ["novel", "first-in-class"]),
    ("BLOCK #7: Do not share syringe", ["Do not share", "single patient use"]),
    ("BLOCK #10: Do not freeze", ["Do not freeze", "freeze", "frozen"]),
    ("BLOCK #21: Discard unused portion", ["Discard", "unused portion", "single-dose"]),
    ("BLOCK #33/34: warm any other way", ["Do not attempt to warm", "warm", "any other way"]),
    ("BLOCK #50: Do not inject into a vein", ["Do not inject into a vein", "Do not administer intravenously", "intravenous"]),
    ("SOFT_FLAG #40/41: always wash hands", ["always wash", "wash your hands", "soap and water"]),
]

for label, terms in SEARCHES:
    print(f"\n{'='*80}")
    print(f"  {label}")
    print(f"{'='*80}")
    for term in terms:
        res = c.scroll(
            collection_name=col,
            scroll_filter=models.Filter(
                must=[models.FieldCondition(key="text", match=models.MatchText(text=term))]
            ),
            limit=5,
            with_payload=["text", "ref_id", "rt_id"],
        )
        pts = res[0]
        if not pts:
            print(f"  '{term}' → NO RESULTS")
            continue
        print(f"  '{term}' → {len(pts)} hits:")
        for pt in pts:
            ref = (pt.payload.get("ref_id") or "?")[:55]
            rt = pt.payload.get("rt_id") or "?"
            txt = pt.payload.get("text", "")
            # Find the matching line
            found_line = ""
            for line in txt.split("\n"):
                if term.lower() in line.lower():
                    found_line = line.strip()[:130]
                    break
            if found_line:
                print(f"    rt={rt} | {ref}")
                print(f"      >> \"{found_line}\"")
            else:
                print(f"    rt={rt} | {ref} | (term in chunk but no single matching line)")

print("\n\nDONE")
