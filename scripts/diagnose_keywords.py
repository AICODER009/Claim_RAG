#!/usr/bin/env python3
"""Diagnose exactly what keyword search does for each blocked claim.
Also check: should these claims actually be substantiated?"""

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
    {"id":"2",  "claim":"You should not inject VYVGART HYTRULO into a vein or muscle.",
     "rewritten":"What evidence supports that VYVGART HYTRULO should not be injected into a vein or muscle?",
     "evidence_search":"inject.*vein.*muscle|intravenous.*intramuscular|Do not administer intravenously"},
    {"id":"3",  "claim":"Do not use VYVGART HYTRULO if it is expired.",
     "rewritten":"What evidence supports avoiding use of VYVGART HYTRULO if it is expired?",
     "evidence_search":"expired|expiration date"},
    {"id":"7",  "claim":"Do not share the prefilled syringe.",
     "rewritten":"What evidence supports the recommendation to not share the prefilled syringe?",
     "evidence_search":"share.*syringe|Do not share"},
    {"id":"10", "claim":"Do not freeze VYVGART HYTRULO.",
     "rewritten":"Should VYVGART HYTRULO be frozen during storage?",
     "evidence_search":"Do not freeze|frozen"},
    {"id":"11", "claim":"Do not use VYVGART HYTRULO if it has been at room temperature for longer than 30 days.",
     "rewritten":"What evidence supports not using VYVGART HYTRULO after more than 30 days at room temperature?",
     "evidence_search":"room temperature.*longer than 30|30 days"},
    {"id":"15", "claim":"For subcutaneous injection over 20 to 30 seconds",
     "rewritten":"What evidence supports subcutaneous injection administration over 20 to 30 seconds?",
     "evidence_search":"20 to 30 seconds"},
    {"id":"21", "claim":"Discard any unused portion",
     "rewritten":"What evidence supports this claim?",
     "evidence_search":"Discard.*unused"},
    {"id":"22", "claim":"First, patients need to check the expiration date.",
     "rewritten":"What evidence supports patients needing to check the expiration date?",
     "evidence_search":"check.*expiration date"},
    {"id":"33", "claim":"Do not attempt to warm the prefilled syringe in any other way.",
     "rewritten":"What evidence supports that prefilled syringes should not be warmed by any method other than the recommended approach?",
     "evidence_search":"warm.*any other way|Do not.*warm"},
    {"id":"41", "claim":"Patients should always wash their hands with soap and water prior to self-injecting",
     "rewritten":"Should patients wash their hands before self-injecting?",
     "evidence_search":"wash.*hands|Wash your hands"},
    {"id":"50", "claim":"Do not inject into a vein.",
     "rewritten":"What evidence supports avoiding intravenous injection for this treatment?",
     "evidence_search":"Do not inject into a vein|intravenous|Do not administer intravenously"},
]


def main():
    cfg = load_config()
    qdrant = QdrantClient(url=cfg.qdrant.url, api_key=cfg.qdrant.api_key, timeout=60)
    collection = cfg.qdrant.collection_name

    print(f"Collection: {collection}")
    print()

    for tc in BLOCKED:
        print("=" * 90)
        print(f"CLAIM #{tc['id']}: \"{tc['claim']}\"")
        print(f"Rewritten: \"{tc['rewritten']}\"")

        # ── KEYWORD EXTRACTION ──
        rw_keywords = extract_keywords(tc["rewritten"])
        claim_keywords = extract_keywords(tc["claim"], max_keywords=30)
        
        # What the pipeline actually uses (only rewritten, no original_claim_text)
        # Since run_50_claims.py does NOT pass original_claim_text
        print(f"\n  Keywords from REWRITTEN query: {rw_keywords}")
        print(f"  Keywords from ORIGINAL claim:  {claim_keywords}")
        print(f"  ⚠️ Pipeline ONLY uses rewritten keywords (original_claim_text not passed)")

        # ── KEYWORD SEARCH SIMULATION ──
        # Simulate what the text search does with JUST the rewritten keywords
        COMMON_CLINICAL = {
            "patients", "treated", "treatment", "study", "clinical",
            "adverse", "reactions", "occurred", "placebo", "compared",
            "versus", "results", "data", "safety", "efficacy",
            "dose", "mg", "administration", "recommended", "use",
            "risk", "events", "reported", "trials", "subjects",
        }
        specific = [kw for kw in rw_keywords if kw not in COMMON_CLINICAL and len(kw) > 2]
        common = [kw for kw in rw_keywords if kw in COMMON_CLINICAL or len(kw) <= 2]
        search_kws = (specific[:8] + common[:4])[:10]
        print(f"  After filtering → search keywords: {search_kws}")

        # Check which of these keywords match chunks with the evidence
        print(f"\n  [KEYWORD HIT TEST] Searching Qdrant for each keyword:")
        for kw in search_kws:
            try:
                results = qdrant.scroll(
                    collection_name=collection,
                    scroll_filter=models.Filter(
                        must=[models.FieldCondition(key="text", match=models.MatchText(text=kw))]
                    ),
                    limit=5,
                    with_payload=["ref_id", "rt_id"],
                )
                hits = len(results[0])
                if hits > 0:
                    refs = set(p.payload.get("ref_id","?")[:35] for p in results[0])
                    print(f"    '{kw}' → {hits}+ hits from: {refs}")
                else:
                    print(f"    '{kw}' → ❌ 0 hits!")
            except Exception as e:
                print(f"    '{kw}' → ERROR: {e}")

        # ── FULL TEXT SEARCH: Does the claim text itself find the evidence? ──
        print(f"\n  [FULL CLAIM TEXT SEARCH] Searching for claim as phrase:")
        # Try searching with key distinctive phrases from the claim
        distinctive = tc["claim"].split(".")[-2] if "." in tc["claim"] else tc["claim"]
        # Search the most distinctive 2-3 word phrase
        words = tc["claim"].lower().replace(".", "").split()
        # Try pairs of distinctive words
        best_phrase = None
        best_hits = []
        for i in range(len(words)):
            for j in range(i+1, min(i+3, len(words))):
                phrase = words[j]  # just individual words
                if len(phrase) > 3 and phrase not in {"should", "their", "always", "first", "that", "this", "into", "been"}:
                    try:
                        res = qdrant.scroll(
                            collection_name=collection,
                            scroll_filter=models.Filter(
                                must=[models.FieldCondition(key="text", match=models.MatchText(text=phrase))]
                            ),
                            limit=3,
                            with_payload=["text", "ref_id"],
                        )
                        for pt in res[0]:
                            txt = pt.payload.get("text", "")
                            if re.search(tc["evidence_search"], txt, re.IGNORECASE):
                                best_phrase = phrase
                                best_hits.append(pt.payload.get("ref_id","?"))
                    except:
                        pass
        
        if best_hits:
            print(f"    ✅ Evidence reachable via keyword '{best_phrase}' in: {set(best_hits)}")
        else:
            print(f"    ❌ Could not find evidence via any single keyword")

        # ── SHOULD IT BE SUBSTANTIATED? ──
        print(f"\n  [SHOULD IT BE SUBSTANTIATED?]")
        # Check if the evidence text actually exists in Qdrant
        found = False
        offset = None
        while True:
            pts, nxt = qdrant.scroll(
                collection_name=collection, limit=250,
                offset=offset, with_payload=True, with_vectors=False,
            )
            for pt in pts:
                text = (pt.payload or {}).get("text", "")
                if re.search(tc["evidence_search"], text, re.IGNORECASE):
                    ref = pt.payload.get("ref_id", "?")
                    # Show the matching line
                    for line in text.split("\n"):
                        if re.search(tc["evidence_search"], line, re.IGNORECASE):
                            print(f"    ✅ YES — Found in Qdrant: ref={ref[:50]}")
                            print(f"       \"{line.strip()[:100]}\"")
                            found = True
                            break
                    if found:
                        break
            if found or nxt is None:
                break
            offset = nxt
        
        if not found:
            print(f"    ❌ NO — Evidence genuinely not in Qdrant. Correctly blocked.")
        print()

    print("=" * 90)
    print("KEY FINDING: Check if `original_claim_text` is passed to retriever")
    print("If not, the keyword search only uses the REWRITTEN query keywords,")
    print("which may lose critical terms like 'freeze', 'expired', 'vein'")


if __name__ == "__main__":
    main()
