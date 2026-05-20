#!/usr/bin/env python3
"""Deep diagnosis: Why are blocked claims failing? Is it retrieval or judge?"""

import json, os, sys, re
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env", override=True)
os.environ["HF_HOME"] = r"D:\hf_cache"
os.environ["TRANSFORMERS_CACHE"] = r"D:\hf_cache"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import torch
from transformers import AutoTokenizer, AutoModel
from qdrant_client import QdrantClient

from new_pipeline.config import load_config
from new_pipeline.retrieval.hybrid_retriever import extract_keywords
from new_pipeline.retrieval.mapping_matrix import MappingMatrix

# Representative blocked claims
TEST_CLAIMS = [
    {"id": "3",  "claim": "Do not use VYVGART HYTRULO if it is expired.", "ct_id": "CT-606", "search": "expired"},
    {"id": "10", "claim": "Do not freeze VYVGART HYTRULO.", "ct_id": "CT-606", "search": "Do not freeze"},
    {"id": "11", "claim": "Do not use VYVGART HYTRULO if it has been at room temperature for longer than 30 days.", "ct_id": "CT-606", "search": "room temperature.*longer than 30"},
    {"id": "33", "claim": "Do not attempt to warm the prefilled syringe in any other way.", "ct_id": "CT-606", "search": "warm.*any other way"},
    {"id": "21", "claim": "Discard any unused portion", "ct_id": "CT-605", "search": "Discard.*unused"},
    {"id": "41", "claim": "Patients should always wash their hands with soap and water prior to self-injecting", "ct_id": "CT-605", "search": "wash.*hands"},
    {"id": "50", "claim": "Do not inject into a vein.", "ct_id": "CT-603", "search": "Do not inject into a vein"},
    {"id": "15", "claim": "For subcutaneous injection over 20 to 30 seconds", "ct_id": "CT-603", "search": "20 to 30 seconds"},
    {"id": "22", "claim": "First, patients need to check the expiration date.", "ct_id": "CT-605", "search": "expiration date"},
]


def main():
    cfg = load_config()
    qdrant = QdrantClient(url=cfg.qdrant.url, api_key=cfg.qdrant.api_key, timeout=60)
    collection = cfg.qdrant.collection_name
    matrix = MappingMatrix(cfg.claim_mapping_path)

    info = qdrant.get_collection(collection)
    print(f"Collection: {collection} | Points: {info.points_count}")

    # Load MedCPT
    print("Loading MedCPT...")
    q_tok = AutoTokenizer.from_pretrained("ncbi/MedCPT-Query-Encoder")
    q_model = AutoModel.from_pretrained("ncbi/MedCPT-Query-Encoder")
    q_model.eval()

    def encode(text):
        with torch.no_grad():
            enc = q_tok(text, max_length=64, truncation=True, padding=True, return_tensors="pt")
            return q_model(**enc).last_hidden_state[:, 0, :][0].tolist()

    print("Ready.\n")

    for tc in TEST_CLAIMS:
        print("=" * 80)
        print(f"CLAIM #{tc['id']}: \"{tc['claim']}\"")
        print(f"CT-ID: {tc['ct_id']}")
        print("-" * 80)

        # ── STEP 1: Does the evidence exist in Qdrant? ──
        print(f"\n[STEP 1] Scanning ALL {info.points_count} chunks for: '{tc['search']}'")
        found_chunks = []
        offset = None
        while True:
            pts, next_offset = qdrant.scroll(
                collection_name=collection, limit=250,
                offset=offset, with_payload=True, with_vectors=False,
            )
            for pt in pts:
                text = (pt.payload or {}).get("text", "")
                if re.search(tc["search"], text, re.IGNORECASE):
                    found_chunks.append({
                        "id": pt.id,
                        "ref_id": (pt.payload or {}).get("ref_id", "?"),
                        "rt_id": (pt.payload or {}).get("rt_id", "?"),
                        "text": text,
                    })
            if next_offset is None:
                break
            offset = next_offset

        if not found_chunks:
            print(f"  ❌ EVIDENCE NOT IN QDRANT — text was never chunked/embedded!")
            print(f"     Root cause: INGESTION/CHUNKING gap")
            print()
            continue

        print(f"  ✅ Found in {len(found_chunks)} chunk(s):")
        for fc in found_chunks[:3]:
            print(f"     • Point {fc['id']} | ref={fc['ref_id'][:50]} | rt={fc['rt_id']}")
            # Show the exact matching line
            for line in fc["text"].split("\n"):
                if re.search(tc["search"], line, re.IGNORECASE):
                    print(f"       Matching line: \"{line.strip()[:100]}\"")
                    break

        # ── STEP 2: Where does dense search rank these chunks? ──
        print(f"\n[STEP 2] Dense search ranking (MedCPT, no filters)")
        claim_vec = encode(tc["claim"])
        dense_all = qdrant.query_points(
            collection_name=collection, query=claim_vec,
            limit=500, with_payload=True,
        )

        expected_ids = {fc["id"] for fc in found_chunks}
        found_ranks = []
        for rank, pt in enumerate(dense_all.points, 1):
            if pt.id in expected_ids:
                found_ranks.append((rank, pt.score, pt.payload.get("ref_id", "?")))

        if found_ranks:
            best_rank, best_score, best_ref = found_ranks[0]
            print(f"  Best rank: #{best_rank} (score: {best_score:.4f}) from {best_ref[:50]}")
            if best_rank > 100:
                print(f"  ⚠️ Rank #{best_rank} > 100 — OUTSIDE dense_top_k=100 retrieval window!")
            elif best_rank > 50:
                print(f"  ⚠️ Rank #{best_rank} > 50 — borderline, might be filtered by RRF")
            else:
                print(f"  ✅ Rank #{best_rank} <= 50 — should be retrieved")
            for r, s, ref in found_ranks[:3]:
                print(f"     Rank #{r} | score={s:.4f} | {ref[:50]}")
        else:
            print(f"  ❌ Expected chunk NOT in top 500 dense results!")

        # Show what IS at top
        print(f"\n  Top 5 dense results (what got retrieved instead):")
        for pt in dense_all.points[:5]:
            in_expected = "⭐" if pt.id in expected_ids else "  "
            print(f"  {in_expected} score={pt.score:.4f} | rt={pt.payload.get('rt_id','?')} | ref={pt.payload.get('ref_id','?')[:45]}")
            print(f"       \"{pt.payload.get('text','')[:80]}...\"")

        # ── STEP 3: Tier filtering check ──
        print(f"\n[STEP 3] Tier filtering for CT-ID={tc['ct_id']}")
        if matrix.has_ct_id(tc["ct_id"]):
            blocked_rts = matrix.get_blocked_rt_ids(tc["ct_id"])
            primary_rts = matrix.get_primary_rt_ids(tc["ct_id"])
            acceptable_rts = matrix.get_acceptable_rt_ids(tc["ct_id"])

            for fc in found_chunks[:3]:
                rt = fc["rt_id"]
                if rt in blocked_rts:
                    print(f"  ❌ RT-ID '{rt}' is BLOCKED (tier N) for {tc['ct_id']}!")
                    print(f"     → This chunk is FILTERED OUT by tier logic!")
                elif rt in primary_rts:
                    print(f"  ✅ RT-ID '{rt}' is PRIMARY tier (P)")
                elif rt in acceptable_rts:
                    print(f"  ✅ RT-ID '{rt}' is ACCEPTABLE tier (A)")
                else:
                    print(f"  ⚠️ RT-ID '{rt}' NOT in mapping matrix for {tc['ct_id']} — no tier boost, no blocking")
        else:
            print(f"  ⚠️ CT-ID '{tc['ct_id']}' not in mapping matrix!")

        # ── STEP 4: Keyword analysis ──
        print(f"\n[STEP 4] Keyword extraction")
        kws = extract_keywords(tc["claim"])
        print(f"  Claim keywords ({len(kws)}): {kws}")

        # Check if keywords match target chunk
        target_text = found_chunks[0]["text"].lower()
        matched_kws = [k for k in kws if k in target_text]
        missed_kws = [k for k in kws if k not in target_text]
        print(f"  Keywords IN target chunk: {len(matched_kws)}/{len(kws)} → {matched_kws}")
        print(f"  Keywords NOT in target:   {missed_kws}")

        # ── DIAGNOSIS ──
        print(f"\n[DIAGNOSIS]")
        if not found_chunks:
            print(f"  ROOT CAUSE: Evidence not in Qdrant (ingestion/chunking gap)")
        elif found_ranks and found_ranks[0][0] > 100:
            print(f"  ROOT CAUSE: Dense embedding mismatch — MedCPT ranks evidence at #{found_ranks[0][0]}")
            print(f"  FIX: MedCPT is trained on biomedical Q&A, not product handling instructions")
        elif any(fc["rt_id"] in matrix.get_blocked_rt_ids(tc["ct_id"]) for fc in found_chunks if matrix.has_ct_id(tc["ct_id"])):
            print(f"  ROOT CAUSE: Tier filtering BLOCKS the evidence RT-ID!")
        elif found_ranks and found_ranks[0][0] <= 20:
            print(f"  ROOT CAUSE: Evidence WAS retrieved (rank #{found_ranks[0][0]}) but JUDGE rejected it")
            print(f"  FIX: Check if judge prompt is too strict or chunk doesn't contain verbatim text")
        else:
            mid_rank = found_ranks[0][0] if found_ranks else "?"
            print(f"  ROOT CAUSE: Evidence at rank #{mid_rank} — in retrieval window but maybe lost after RRF/filtering")
        print()

    print("=" * 80)
    print("INVESTIGATION COMPLETE")


if __name__ == "__main__":
    main()
