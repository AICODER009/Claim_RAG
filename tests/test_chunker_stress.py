"""Stress-test chunker on ALL 86 documents — find every failure mode."""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\revisto_evidence_aligned_clean")

from pathlib import Path
from new_pipeline.ingestion.preprocessor import preprocess
from new_pipeline.ingestion.chunker import MarkdownChunker

PARSED_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\LLamaParser")
chunker = MarkdownChunker(target_tokens=400, max_tokens=500, min_tokens=50)

all_files = sorted(PARSED_DIR.glob("*.md"))
total_chunks = 0
problems_found = []

for fpath in all_files:
    raw = fpath.read_text(encoding="utf-8")
    clean = preprocess(raw, filename=fpath.stem)
    chunks = chunker.chunk(clean, filename=fpath.stem)

    types = {}
    for c in chunks:
        types[c.segment_type] = types.get(c.segment_type, 0) + 1
    tokens = [c.approx_tokens for c in chunks]
    no_section = sum(1 for c in chunks if not c.section)
    total_chunks += len(chunks)

    # Check for problems
    issues = []
    oversized = [c for c in chunks if c.approx_tokens > 512]
    tiny = [c for c in chunks if c.approx_tokens < 3 and c.segment_type == "text"]
    if oversized:
        issues.append(f"{len(oversized)} chunks >512tok (max={max(c.approx_tokens for c in oversized)})")
    if tiny:
        issues.append(f"{len(tiny)} near-empty text chunks")
    if no_section > len(chunks) * 0.7:
        issues.append(f"{no_section}/{len(chunks)} chunks have no section")

    # Check for markdown pipe tables that chunker may miss
    pipe_table_lines = sum(1 for l in clean.split("\n") if l.strip().startswith("|") and l.count("|") >= 3)
    if pipe_table_lines > 5 and types.get("table", 0) == 0:
        issues.append(f"MISSED: {pipe_table_lines} pipe-table lines but 0 table chunks")

    if issues:
        problems_found.append((fpath.name, issues, types, tokens))

# Print problems
print(f"=== STRESS TEST: {len(all_files)} files, {total_chunks} total chunks ===\n")
print(f"Files with issues: {len(problems_found)}/{len(all_files)}\n")

for fname, issues, types, tokens in problems_found:
    print(f"!! {fname[:55]}")
    print(f"   chunks={sum(types.values())}  types={types}  avg={sum(tokens)//max(len(tokens),1)}tok")
    for issue in issues:
        print(f"   -> {issue}")
    print()

# Summary stats
print(f"\n=== SUMMARY ===")
print(f"Total files: {len(all_files)}")
print(f"Total chunks: {total_chunks}")
print(f"Files with problems: {len(problems_found)}")
print(f"Clean files: {len(all_files) - len(problems_found)}")
