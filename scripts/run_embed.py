"""Embed all embeddable chunks using MedCPT Article Encoder.

Reads each .chunks.json file, embeds text of embeddable chunks,
saves the 768-dim vector back into the JSON record.

Skips non-embeddable chunks (reference, figure) — their vector stays [].
Skips chunks that already have a populated vector (idempotent re-runs).
"""
import os, sys, json, time, logging

# Redirect ALL HuggingFace caches to D: drive (C: has <5MB free)
os.environ["HF_HOME"] = r"D:\hf_cache"
os.environ["HF_HUB_CACHE"] = r"D:\hf_cache\hub"
os.environ["HUGGINGFACE_HUB_CACHE"] = r"D:\hf_cache\hub"
os.environ["TRANSFORMERS_CACHE"] = r"D:\hf_cache\hub"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\revisto_evidence_aligned_clean")

import numpy as np
import torch
from pathlib import Path
# Using direct model loading (not MedCPTEmbedder) to save RAM

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\chunks_final")
BATCH_SIZE = 16  # Smaller batches to limit RAM usage on CPU

def main():
    # Detect device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")

    # Use article-only loader to save RAM (skip Query Encoder)
    logger.info("Loading MedCPT Article Encoder only (lightweight mode)...")
    
    from transformers import AutoModel, AutoTokenizer
    
    article_tokenizer = AutoTokenizer.from_pretrained(
        "ncbi/MedCPT-Article-Encoder"
    )
    article_model = AutoModel.from_pretrained(
        "ncbi/MedCPT-Article-Encoder"
    ).to(device).eval()
    
    logger.info("Article Encoder loaded.")

    files = sorted(OUT_DIR.glob("*.chunks.json"))
    logger.info(f"Found {len(files)} chunk files")

    total_embedded = 0
    total_skipped = 0
    total_already = 0
    start = time.time()

    for fi, jf in enumerate(files):
        data = json.loads(jf.read_text(encoding="utf-8"))

        # Collect embeddable chunks that need vectors
        to_embed = []
        indices = []
        for i, c in enumerate(data):
            if not c.get("embeddable", False):
                total_skipped += 1
                continue
            if c.get("vector") and len(c["vector"]) > 0:
                total_already += 1
                continue
            to_embed.append(c["text"])
            indices.append(i)

        if not to_embed:
            logger.info(f"[{fi+1}/{len(files)}] {jf.stem[:50]} — nothing to embed")
            continue

        # Batch encode using direct model
        all_vecs = []
        with torch.no_grad():
            for bi in range(0, len(to_embed), BATCH_SIZE):
                batch = to_embed[bi:bi+BATCH_SIZE]
                encoded = article_tokenizer(
                    batch, max_length=512, padding=True,
                    truncation=True, return_tensors="pt"
                ).to(device)
                output = article_model(**encoded)
                vecs = output.last_hidden_state[:, 0, :].cpu().numpy()
                all_vecs.append(vecs)
        vectors = np.vstack(all_vecs)

        # Write vectors back
        for idx, vec in zip(indices, vectors):
            data[idx]["vector"] = vec.tolist()

        # Save
        jf.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        total_embedded += len(to_embed)

        elapsed = time.time() - start
        rate = total_embedded / max(1, elapsed)
        logger.info(
            f"[{fi+1}/{len(files)}] {jf.stem[:45]:45s} "
            f"embedded={len(to_embed):3d}  "
            f"total={total_embedded}  "
            f"rate={rate:.1f} chunks/s"
        )

    elapsed = time.time() - start
    logger.info(f"\nDone in {elapsed:.1f}s")
    logger.info(f"Embedded: {total_embedded}")
    logger.info(f"Skipped (non-embeddable): {total_skipped}")
    logger.info(f"Already had vectors: {total_already}")
    logger.info(f"Output: {OUT_DIR}")

if __name__ == "__main__":
    main()
