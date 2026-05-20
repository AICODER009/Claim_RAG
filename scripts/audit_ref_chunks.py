"""Audit reference chunks — can they cause false matches?

Key risks:
1. Reference numbers (e.g., page "945-55") matching clinical claims ("945 patients")
2. Year numbers ("2024") matching dosage data
3. Volume/issue numbers matching clinical values
4. Secondary reference text containing OTHER papers' data
5. Numbers from cited papers leaking into retrieval
"""
import sys, json, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

OUT_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\chunks_final")

# Analyze ALL reference chunks across corpus
all_ref_chunks = []
all_text_chunks = []
all_table_chunks = []

for jf in sorted(OUT_DIR.glob("*.chunks.json")):
    data = json.loads(jf.read_text(encoding="utf-8"))
    for r in data:
        if r["segment_type"] == "reference":
            all_ref_chunks.append(r)
        elif r["segment_type"] == "text":
            all_text_chunks.append(r)
        elif r["segment_type"] == "table":
            all_table_chunks.append(r)

print("=" * 70)
print("REFERENCE CHUNK AUDIT")
print("=" * 70)
print(f"\nTotal chunks: text={len(all_text_chunks)}, table={len(all_table_chunks)}, reference={len(all_ref_chunks)}")
print(f"Reference chunks: {len(all_ref_chunks)} ({100*len(all_ref_chunks)/(len(all_ref_chunks)+len(all_text_chunks)+len(all_table_chunks)):.0f}% of corpus)")

# ---- RISK 1: How many numeric tokens do reference chunks have? ----
ref_numerics = sum(len(r.get("numeric_tokens", [])) for r in all_ref_chunks)
text_numerics = sum(len(r.get("numeric_tokens", [])) for r in all_text_chunks)
table_numerics = sum(len(r.get("numeric_tokens", [])) for r in all_table_chunks)

print(f"\nNumeric tokens:")
print(f"  text chunks:  {text_numerics:6d}  ({text_numerics/max(1,len(all_text_chunks)):.1f}/chunk)")
print(f"  table chunks: {table_numerics:6d}  ({table_numerics/max(1,len(all_table_chunks)):.1f}/chunk)")
print(f"  ref chunks:   {ref_numerics:6d}  ({ref_numerics/max(1,len(all_ref_chunks)):.1f}/chunk)")

# ---- RISK 2: Sample reference chunks — what do they look like? ----
print(f"\n--- SAMPLE REFERENCE CHUNKS ---")
import random
random.seed(42)
samples = random.sample(all_ref_chunks, min(5, len(all_ref_chunks)))
for r in samples:
    print(f"\n  [{r['ref_id'][:40]}] chunk-{r['chunk_index']:04d}")
    print(f"  text: {r['text'][:150]}...")
    nums = r.get("numeric_tokens", [])
    if nums:
        print(f"  numerics ({len(nums)}): {[n['value'] for n in nums[:8]]}")

# ---- RISK 3: Overlap analysis — ref numbers that match text/table numbers ----
print(f"\n--- FALSE MATCH RISK ANALYSIS ---")

# Collect all numeric values from text/table chunks
clinical_nums = set()
for c in all_text_chunks + all_table_chunks:
    for n in c.get("numeric_tokens", []):
        clinical_nums.add(n["value"])

# Collect all numeric values from reference chunks
ref_nums = set()
for c in all_ref_chunks:
    for n in c.get("numeric_tokens", []):
        ref_nums.add(n["value"])

overlap = clinical_nums & ref_nums
unique_to_refs = ref_nums - clinical_nums

print(f"  Clinical numbers (text+table): {len(clinical_nums)} unique values")
print(f"  Reference numbers:             {len(ref_nums)} unique values")
print(f"  Overlap (potential false matches): {len(overlap)}")
print(f"  Unique to refs only:           {len(unique_to_refs)}")

# ---- RISK 4: Can a ref chunk rank higher than a text chunk for a claim? ----
# Simulate: "21% of patients had relapse"
print(f"\n--- SIMULATED CLAIM: '21% of patients had relapse' ---")
claim_num = "21%"
matching_text = [c for c in all_text_chunks if any(n["value"] == claim_num for n in c.get("numeric_tokens", []))]
matching_ref = [c for c in all_ref_chunks if any(n["value"] == claim_num for n in c.get("numeric_tokens", []))]
matching_table = [c for c in all_table_chunks if any(n["value"] == claim_num for n in c.get("numeric_tokens", []))]

print(f"  text chunks with '21%':  {len(matching_text)}")
print(f"  table chunks with '21%': {len(matching_table)}")
print(f"  ref chunks with '21%':   {len(matching_ref)}")

if matching_ref:
    print(f"  REF CHUNK EXAMPLES:")
    for r in matching_ref[:3]:
        print(f"    [{r['ref_id'][:30]}] {r['text'][:100]}...")

# ---- RISK 5: What types of numbers do refs contain? ----
print(f"\n--- REFERENCE NUMBER TYPES ---")
ref_num_types = {"years": 0, "page_ranges": 0, "volumes": 0, "other": 0}
year_pattern = re.compile(r"^(19|20)\d\d$")
for c in all_ref_chunks:
    for n in c.get("numeric_tokens", []):
        v = n["value"]
        ctx = n.get("context", "")
        if year_pattern.match(v):
            ref_num_types["years"] += 1
        elif re.match(r"^\d{1,4}$", v) and any(w in ctx.lower() for w in ["vol", "pp", "page", ";", ":"]):
            ref_num_types["page_ranges"] += 1
        else:
            ref_num_types["other"] += 1

for k, v in ref_num_types.items():
    print(f"  {k}: {v}")

# ---- RISK 6: Secondary reference problem ----
print(f"\n--- SECONDARY REFERENCE RISK ---")
# Check if any reference chunk contains clinical data (numbers with clinical context)
clinical_keywords = ["patient", "mg", "dose", "efficacy", "hazard", "ratio", "CI", "relapse", "adverse"]
suspicious = []
for c in all_ref_chunks:
    text = c["text"].lower()
    hits = [kw for kw in clinical_keywords if kw.lower() in text]
    if len(hits) >= 2:
        suspicious.append((c["ref_id"], c["chunk_index"], hits, c["text"][:100]))

print(f"  Ref chunks with clinical-sounding text: {len(suspicious)}/{len(all_ref_chunks)}")
if suspicious:
    for ref_id, idx, hits, text in suspicious[:5]:
        print(f"    [{ref_id[:30]}] chunk-{idx:04d}: keywords={hits}")
        print(f"      text: {text}...")
