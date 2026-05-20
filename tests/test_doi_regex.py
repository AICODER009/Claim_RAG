"""Test DOI regex fix on multiple docs."""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\revisto_evidence_aligned_clean")
from pathlib import Path
from new_pipeline.ingestion.metadata_extractor import MetadataExtractor
from new_pipeline.ingestion.preprocessor import preprocess

PARSED = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\LLamaParser")

ext = MetadataExtractor.__new__(MetadataExtractor)

test_files = [
    "Allen_Lancet Neuro_2024.md",
    "Hughes R 2001_Ann Neurol.md",
    "Broers 2019.md",
    "Argenx BVBA.md",
    "Doneddu 2020 J Neurol Neurosurg Psychiatry.md",
    "vyvgart-hytrulo-prescribing-information_3.26.md",
    "Hargraves AAN 2025.md",
    "Van den Bergh_Eur J Neurol_2021.md",
]

for fname in test_files:
    fp = PARSED / fname
    if not fp.exists():
        continue
    raw = fp.read_text(encoding="utf-8")
    clean = preprocess(raw, filename=fp.stem)
    r = ext.extract_without_llm(clean, filename=fp.stem)
    doi = r.get("doi", "---")
    year = r.get("year", "?")
    trial = r.get("trial_id", "---")
    print(f"{fp.stem[:45]:45s}  doi={doi[:40]:40s}  year={year}  trial={trial}")
