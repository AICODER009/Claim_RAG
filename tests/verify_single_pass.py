"""Verify single-pass output quality."""
import sys, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

OUT_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\chunks_final")

# Check Allen 2024
data = json.loads((OUT_DIR / "Allen_Lancet Neuro_2024.chunks.json").read_text(encoding="utf-8"))

print("=== Allen 2024: Structure ===")
types = {}
for r in data:
    types[r["segment_type"]] = types.get(r["segment_type"], 0) + 1
print(f"  Total: {len(data)} chunks")
print(f"  Types: {types}")

meta = data[0]["doc_metadata"]
print(f"  Metadata title: {meta.get('title', 'MISSING')[:80]}")
print(f"  Metadata year: {meta.get('year', 'MISSING')}")
print(f"  Metadata doi: {meta.get('doi', 'MISSING')}")
print(f"  Metadata authors: {str(meta.get('authors_str', 'MISSING'))[:60]}")

# Text chunk with relapse data
text_c = [r for r in data if r["segment_type"] == "text" and "relapse" in r["text"].lower()]
if text_c:
    r = text_c[0]
    print(f"\n=== TEXT CHUNK [{r['chunk_index']}] ===")
    print(f"  section: {r['section'][:60]}")
    print(f"  text: {r['text'][:250]}...")
    print(f"  tokens: {r['approx_tokens']}")
    print(f"  numerics: {len(r['numeric_tokens'])}")
    print(f"  source_table_html: {r['source_table_html']}")

# Table chunk
table_c = [r for r in data if r["segment_type"] == "table"]
if table_c:
    r = table_c[0]
    print(f"\n=== TABLE CHUNK [{r['chunk_index']}] (linearized) ===")
    print(f"  section: {r['section'][:60]}")
    print(f"  text: {r['text'][:350]}...")
    print(f"  tokens: {r['approx_tokens']}")
    print(f"  numerics: {len(r['numeric_tokens'])}")
    has_html = r["source_table_html"] is not None
    print(f"  source_table_html preserved: {has_html} ({len(r['source_table_html']) if has_html else 0} chars)")

# VYVGART PI
pi_data = json.loads((OUT_DIR / "vyvgart-hytrulo-prescribing-information_3.26.chunks.json").read_text(encoding="utf-8"))
pi_meta = pi_data[0]["doc_metadata"]
print(f"\n=== VYVGART PI ===")
print(f"  title: {pi_meta.get('title', 'MISSING')}")
print(f"  year: {pi_meta.get('year', 'MISSING')}")
print(f"  rt_id: {pi_data[0]['rt_id']}")
pi_tables = [r for r in pi_data if r["source_table_html"]]
print(f"  tables linearized: {len(pi_tables)}")
if pi_tables:
    print(f"  sample linearized: {pi_tables[0]['text'][:200]}...")

# Hargraves poster
hg_data = json.loads((OUT_DIR / "Hargraves AAN 2025.chunks.json").read_text(encoding="utf-8"))
hg_meta = hg_data[0]["doc_metadata"]
print(f"\n=== Hargraves Poster ===")
print(f"  title: {hg_meta.get('title', 'MISSING')[:80]}")
print(f"  authors: {str(hg_meta.get('authors_str', 'MISSING'))[:60]}")
print(f"  rt_id: {hg_data[0]['rt_id']}")
print(f"  chunks: {len(hg_data)}")
