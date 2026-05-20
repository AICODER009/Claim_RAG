"""Trace AND-match search step-by-step for the 8 blocked claims.
Shows EXACTLY what keywords are extracted, what Qdrant queries run,
and how many chunks match at each relaxation level."""

import sys, os, re
sys.path.insert(0, "D:\\pip_packages")
from qdrant_client import QdrantClient, models
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env", override=True)
client = QdrantClient(
    url=os.getenv("QDRANT_URL"), 
    api_key=os.getenv("QDRANT_API_KEY"), 
    timeout=30
)
COLLECTION = "verifai_mlr"

# Same extract_keywords function as in hybrid_retriever.py — GENERIC, no claim-specific logic
def extract_keywords(text, max_keywords=10):
    STOPWORDS = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "dare", "ought",
        "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "out", "off", "over", "under", "again",
        "further", "then", "once", "here", "there", "when", "where",
        "why", "how", "all", "each", "every", "both", "few", "more",
        "most", "other", "some", "such", "no", "nor", "not", "only",
        "own", "same", "so", "than", "too", "very", "just", "because",
        "but", "and", "or", "if", "while", "that", "this", "what",
        "which", "who", "whom", "these", "those", "it", "its",
    }
    tokens = re.findall(r"[a-zA-Z0-9]+(?:\.[0-9]+)?%?", text.lower())
    keywords = [t for t in tokens if t not in STOPWORDS and len(t) >= 2]
    seen = set()
    unique = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique.append(kw)
    return unique[:max_keywords]

# Same noise filter as in _and_match_search
NOISE = {
    "evidence", "supports", "support", "supporting", "claim",
    "avoiding", "recommendation", "approach", "method",
    "according", "regarding", "concerning", "suggests",
    "patients", "treated", "treatment", "study", "clinical",
}

# Test claims — a MIX of the blocked ones AND some random other types
# to prove AND-match works generically
TEST_CLAIMS = [
    # The 5 previously-blocked retrieval failures
    "Do not freeze VYVGART HYTRULO.",
    "Do not attempt to warm the prefilled syringe in any other way.",
    "Do not attempt to warm the filled syringe in any other way.",
    "Discard any unused portion",
    "Do not inject into a vein.",
    # Additional DIVERSE claims to prove no overfitting
    "VYVGART HYTRULO is for subcutaneous use only.",
    "Store in refrigerator at 2°C to 8°C.",
    "The most common adverse reactions are infections.",
    "CIDP is a chronic autoimmune disorder.",  # no product name
    "Wash your hands with soap and water.",     # generic instruction
]

print("=" * 80)
print("AND-MATCH SEARCH TRACE — Proving It's Generic, Not Overfitting")
print("=" * 80)

for claim in TEST_CLAIMS:
    print(f"\n{'─' * 70}")
    print(f"CLAIM: \"{claim}\"")
    print(f"{'─' * 70}")
    
    # Step 1: Extract keywords (SAME generic function for ALL claims)
    all_kws = extract_keywords(claim, max_keywords=30)
    print(f"  1. extract_keywords() → {all_kws}")
    
    # Step 2: Filter noise (SAME generic filter for ALL claims)
    specific_kws = [kw for kw in all_kws if kw.lower() not in NOISE and len(kw) >= 3][:8]
    print(f"  2. After noise filter  → {specific_kws}")
    
    # Step 3: Progressive relaxation
    print(f"  3. AND-match relaxation:")
    for n in range(len(specific_kws), 0, -1):
        subset = specific_kws[:n]
        
        # Build AND filter: ALL keywords must appear in chunk text
        text_conditions = [
            models.FieldCondition(key="text", match=models.MatchText(text=kw))
            for kw in subset
        ]
        
        try:
            results = client.scroll(
                collection_name=COLLECTION,
                scroll_filter=models.Filter(must=text_conditions),
                limit=20,
                with_payload=True,
            )
            points = results[0]
            
            # Count by source
            sources = {}
            for p in points:
                ref = p.payload.get("ref_id", "?")[:40]
                sources[ref] = sources.get(ref, 0) + 1
            
            source_str = ", ".join(f"{v}×{k}" for k, v in sorted(sources.items(), key=lambda x: -x[1])[:5])
            
            print(f"     Level {n}/{len(specific_kws)}: AND({subset})")
            print(f"       → {len(points)} chunks matched  |  Sources: {source_str}")
            
            # Show preview of top matches
            for j, p in enumerate(points[:3]):
                ref = p.payload.get("ref_id", "?")[:35]
                section = p.payload.get("section", "?")[:50]
                text = p.payload.get("text", "")[:80].replace("\n", " ")
                print(f"       [{j+1}] {ref} | {section}")
                print(f"           \"{text}...\"")
            
            if len(points) >= 3:
                print(f"       ✅ Got ≥3 results → STOP relaxation")
                break
            else:
                print(f"       ⚠️ Only {len(points)} results → continue relaxing...")
                
        except Exception as e:
            print(f"       ERROR: {e}")

print(f"\n{'=' * 80}")
print("CONCLUSION: The same extract_keywords() + AND-filter + relaxation")
print("logic runs identically for ALL claims. No claim-specific rules exist.")
print("=" * 80)
