#!/usr/bin/env python3
"""Quick test: Verify keyword search fix works for blocked claims.
Does NOT load MedCPT — just tests the keyword extraction + text search path."""

import json, os, sys, re
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env", override=True)
os.environ["HF_HOME"] = r"D:\hf_cache"

from qdrant_client import QdrantClient, models
from new_pipeline.config import load_config
from new_pipeline.retrieval.hybrid_retriever import extract_keywords

BLOCKED = [
    {"id":"3",  "claim":"Do not use VYVGART HYTRULO if it is expired.", "search":"expired"},
    {"id":"10", "claim":"Do not freeze VYVGART HYTRULO.", "search":"Do not freeze"},
    {"id":"11", "claim":"Do not use VYVGART HYTRULO if it has been at room temperature for longer than 30 days.", "search":"room temperature.*longer than 30"},
    {"id":"21", "claim":"Discard any unused portion", "search":"Discard.*unused"},
    {"id":"33", "claim":"Do not attempt to warm the prefilled syringe in any other way.", "search":"warm.*any other way"},
    {"id":"41", "claim":"Patients should always wash their hands with soap and water prior to self-injecting", "search":"wash.*hands"},
]


def main():
    cfg = load_config()
    qdrant = QdrantClient(url=cfg.qdrant.url, api_key=cfg.qdrant.api_key, timeout=60)
    collection = cfg.qdrant.collection_name

    # Simulate what the FIXED pipeline does:
    # 1. Rewritten query keywords + original claim keywords + stem expansion
    REWRITER_NOISE = {
        "evidence", "supports", "support", "supporting", "claim",
        "avoiding", "recommendation", "approach", "method",
        "according", "regarding", "concerning", "suggests",
    }
    COMMON_CLINICAL = {
        "patients", "treated", "treatment", "study", "clinical",
        "adverse", "reactions", "occurred", "placebo", "compared",
        "versus", "results", "data", "safety", "efficacy",
        "dose", "mg", "administration", "recommended", "use",
        "risk", "events", "reported", "trials", "subjects",
    }
    ALL_NOISE = REWRITER_NOISE | COMMON_CLINICAL

    fake_rewrites = {
        "3":  "What evidence supports avoiding use of VYVGART HYTRULO if it is expired?",
        "10": "Should VYVGART HYTRULO be frozen during storage?",
        "11": "What evidence supports not using VYVGART HYTRULO after more than 30 days at room temperature?",
        "21": "What evidence supports this claim?",
        "33": "What evidence supports that prefilled syringes should not be warmed by any method other than the recommended approach?",
        "41": "Should patients wash their hands before self-injecting?",
    }

    for tc in BLOCKED:
        print("=" * 80)
        print(f"CLAIM #{tc['id']}: \"{tc['claim']}\"")

        rewrite = fake_rewrites[tc['id']]
        rw_keywords = extract_keywords(rewrite)
        claim_keywords = extract_keywords(tc['claim'], max_keywords=30)

        # Merge (what the fixed pipeline does)
        merged = list(rw_keywords)
        seen = set(rw_keywords)
        for kw in claim_keywords:
            if kw not in seen:
                merged.append(kw)
                seen.add(kw)

        print(f"  BEFORE FIX (rewrite only): {rw_keywords}")
        print(f"  AFTER FIX (merged):        {merged}")

        # Filter noise
        specific = [kw for kw in merged if kw not in ALL_NOISE and len(kw) > 2]
        print(f"  After noise filter:        {specific}")

        # Stem expansion
        expanded = set(specific)
        for kw in specific:
            if kw.endswith("ed"):
                expanded.add(kw[:-2])
                expanded.add(kw[:-2] + "e")
                expanded.add(kw[:-2] + "ing")
            elif kw.endswith("en"):
                expanded.add(kw[:-2])
                expanded.add(kw[:-2] + "e")
                if kw == "frozen": expanded.add("freeze")
            elif kw.endswith("ing"):
                expanded.add(kw[:-3])
                expanded.add(kw[:-3] + "e")
                expanded.add(kw[:-3] + "ed")
            elif kw.endswith("s") and not kw.endswith("ss"):
                expanded.add(kw[:-1])
            elif kw.endswith("tion"):
                expanded.add(kw[:-4] + "t")
                expanded.add(kw[:-4] + "ted")
        expanded = {k for k in expanded if len(k) >= 3}
        print(f"  After stem expansion:      {sorted(expanded)}")

        # Test: do these expanded keywords find the target evidence?
        print(f"\n  Searching Qdrant for evidence matching: '{tc['search']}'")
        found_evidence = False
        for kw in sorted(expanded):
            try:
                res = qdrant.scroll(
                    collection_name=collection,
                    scroll_filter=models.Filter(
                        must=[models.FieldCondition(key="text", match=models.MatchText(text=kw))]
                    ),
                    limit=10,
                    with_payload=["text", "ref_id"],
                )
                for pt in res[0]:
                    text = pt.payload.get("text", "")
                    if re.search(tc["search"], text, re.IGNORECASE):
                        print(f"    ✅ '{kw}' → FOUND evidence in: {pt.payload.get('ref_id','?')[:50]}")
                        for line in text.split("\n"):
                            if re.search(tc["search"], line, re.IGNORECASE):
                                print(f"       \"{line.strip()[:80]}\"")
                                break
                        found_evidence = True
                        break
            except:
                pass
            if found_evidence:
                break

        if not found_evidence:
            # Try each keyword without evidence regex match
            hits = {}
            for kw in sorted(expanded):
                try:
                    res = qdrant.scroll(
                        collection_name=collection,
                        scroll_filter=models.Filter(
                            must=[models.FieldCondition(key="text", match=models.MatchText(text=kw))]
                        ),
                        limit=3,
                        with_payload=["ref_id"],
                    )
                    if res[0]:
                        hits[kw] = len(res[0])
                except:
                    pass
            print(f"    ⚠️ No direct match, but keyword hits: {hits}")
        print()

    print("DONE")


if __name__ == "__main__":
    main()
