"""Analyze mid-sentence splits — do they cause retrieval problems?"""
import sys, json, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

OUT_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\chunks_final")
data = json.loads((OUT_DIR / "Allen_Lancet Neuro_2024.chunks.json").read_text(encoding="utf-8"))

text_chunks = [c for c in data if c["segment_type"] == "text"]

splits = []
for i, c in enumerate(text_chunks):
    text = c["text"].rstrip()
    if text and text[-1] not in '.!?:;)]"0123456789%':
        next_c = text_chunks[i+1] if i+1 < len(text_chunks) else None
        splits.append((c, next_c))

print("=== MID-SENTENCE SPLIT EXAMPLES (Allen 2024) ===")
print(f"Total text chunks: {len(text_chunks)}, Mid-splits: {len(splits)}")

for c, nc in splits[:4]:
    idx = c["chunk_index"]
    tok = c["approx_tokens"]
    print(f"\n--- chunk-{idx:04d} ({tok} tokens) ---")
    print(f"  ENDS WITH: ...{c['text'][-100:]}")
    if nc:
        clean = re.sub(r"^\[.*?\]\s*", "", nc["text"])
        print(f"  NEXT STARTS: {clean[:100]}...")
    # Check if the split breaks a clinical fact
    nums_in_chunk = [n["value"] for n in c.get("numeric_tokens", [])]
    print(f"  Numbers in this chunk: {nums_in_chunk[:6]}")

# KEY QUESTION: Can a split break a claim match?
print("\n\n=== RETRIEVAL IMPACT ANALYSIS ===")
print("Claim: 'Efgartigimod reduced relapse with HR 0.39'")
print()

# Find ALL chunks containing 0.39
matching = [c for c in data if c["embeddable"] and "0.39" in c["text"]]
print(f"Chunks containing '0.39': {len(matching)}")
for c in matching:
    print(f"  chunk-{c['chunk_index']:04d} ({c['segment_type']}): ...{c['text'][max(0, c['text'].index('0.39')-40):c['text'].index('0.39')+40]}...")

# Find chunks that WOULD match via MedCPT (semantic similarity)
print("\nChunks containing 'relapse' + 'efgartigimod':")
semantic = [c for c in data if c["embeddable"] and "relapse" in c["text"].lower() and "efgartigimod" in c["text"].lower()]
print(f"  {len(semantic)} chunks")
for c in semantic[:3]:
    print(f"  chunk-{c['chunk_index']:04d}: {c['text'][:120]}...")

# Show a real mid-split case with the continuation
print("\n\n=== WORST CASE: data split across boundary ===")
for c, nc in splits:
    # Find splits where a number appears at the very end
    nums = c.get("numeric_tokens", [])
    if nums:
        last_num = nums[-1]
        pos = c["text"].rfind(last_num["value"])
        if pos > len(c["text"]) - 30:  # Number near the end
            print(f"\nchunk-{c['chunk_index']:04d} ends near number '{last_num['value']}':")
            print(f"  END: ...{c['text'][-80:]}")
            if nc:
                clean = re.sub(r"^\[.*?\]\s*", "", nc["text"])
                print(f"  NEXT: {clean[:80]}...")
            print(f"  IS THE NUMBER IN THIS CHUNK? YES (captured in numeric_tokens)")
            break
