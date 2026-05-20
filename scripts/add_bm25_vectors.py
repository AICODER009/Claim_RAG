#!/usr/bin/env python3
"""Create a separate BM25 collection and index all chunks.

Approach: Two-collection hybrid search
  - verifai_mlr      → dense MedCPT vectors (existing, untouched)
  - verifai_mlr_bm25 → BM25 sparse vectors (new)

Both collections share the same point IDs and payloads.
At search time: query both, RRF-fuse the results.
"""

import sys, os, types, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Stub onnxruntime (BM25 doesn't need ONNX)
ort_mock = types.ModuleType("onnxruntime")
ort_mock.SessionOptions = type("SessionOptions", (), {})
ort_mock.InferenceSession = type("InferenceSession", (), {})
ort_mock.GraphOptimizationLevel = type("GraphOptimizationLevel", (), {"ORT_ENABLE_ALL": 99})
sys.modules["onnxruntime"] = ort_mock
sys.modules["onnxruntime.capi"] = types.ModuleType("onnxruntime.capi")
sys.modules["onnxruntime.capi._pybind_state"] = types.ModuleType("onnxruntime.capi._pybind_state")

sys.path.insert(0, "D:\\pip_packages")
sys.path.insert(0, str(os.path.join(os.path.dirname(__file__), "..", "..")))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)
os.environ["HF_HOME"] = r"D:\hf_cache"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from qdrant_client import QdrantClient, models
from fastembed.sparse.bm25 import Bm25
from new_pipeline.config import load_config


BM25_COLLECTION = "verifai_mlr_bm25"


def main():
    cfg = load_config()
    client = QdrantClient(url=cfg.qdrant.url, api_key=cfg.qdrant.api_key, timeout=120)
    source_collection = cfg.qdrant.collection_name

    info = client.get_collection(source_collection)
    total_points = info.points_count
    print(f"Source collection: {source_collection} | Points: {total_points}")

    # ── Step 1: Create BM25 collection ──
    print(f"\n[Step 1] Creating BM25 collection: {BM25_COLLECTION}")
    try:
        existing = client.get_collection(BM25_COLLECTION)
        print(f"  Collection exists: {existing.points_count} points")
        if existing.points_count == total_points:
            print(f"  ✅ Already fully indexed! Skipping to verification.")
            skip_indexing = True
        else:
            print(f"  ⚠️ Partial: {existing.points_count}/{total_points}. Will continue indexing.")
            skip_indexing = False
    except Exception:
        # Create new collection with ONLY sparse vectors
        client.create_collection(
            collection_name=BM25_COLLECTION,
            vectors_config={},  # No dense vectors
            sparse_vectors_config={
                "bm25": models.SparseVectorParams(
                    modifier=models.Modifier.IDF,
                )
            },
            on_disk_payload=True,
        )
        print(f"  ✅ Created with sparse BM25 config (modifier=IDF)")
        skip_indexing = False

        # Create payload indexes for filtering (same as source)
        for field, schema_type in [
            ("rt_id", models.PayloadSchemaType.KEYWORD),
            ("ref_id", models.PayloadSchemaType.KEYWORD),
            ("ref_category", models.PayloadSchemaType.KEYWORD),
            ("segment_type", models.PayloadSchemaType.KEYWORD),
        ]:
            try:
                client.create_payload_index(
                    collection_name=BM25_COLLECTION,
                    field_name=field,
                    field_schema=schema_type,
                )
            except:
                pass
        print(f"  ✅ Payload indexes created")

    # ── Step 2: Load BM25 model ──
    print(f"\n[Step 2] Loading fastembed Qdrant/bm25...")
    bm25 = Bm25(model_name="Qdrant/bm25", cache_dir=r"D:\hf_cache")
    print(f"  ✅ Loaded")

    if skip_indexing:
        pass
    else:
        # ── Step 3: Index all chunks ──
        print(f"\n[Step 3] Indexing {total_points} chunks...")
        batch_size = 64
        processed = 0
        offset = None
        t0 = time.time()

        while True:
            points, next_offset = client.scroll(
                collection_name=source_collection,
                limit=batch_size,
                offset=offset,
                with_payload=True,  # Copy all payloads
                with_vectors=False,  # Don't need dense vectors
            )

            if not points:
                break

            texts = []
            upsert_points = []
            for pt in points:
                text = (pt.payload or {}).get("text", "")
                texts.append(text if text.strip() else " ")

            # Batch encode
            sparse_vecs = list(bm25.embed(texts))

            for pt, svec in zip(points, sparse_vecs):
                upsert_points.append(
                    models.PointStruct(
                        id=pt.id,  # SAME ID as source
                        vector={
                            "bm25": models.SparseVector(
                                indices=svec.indices.tolist(),
                                values=svec.values.tolist(),
                            )
                        },
                        payload=pt.payload,  # Copy full payload
                    )
                )

            client.upsert(
                collection_name=BM25_COLLECTION,
                points=upsert_points,
            )

            processed += len(points)
            elapsed = time.time() - t0
            rate = processed / max(elapsed, 0.1)
            eta = (total_points - processed) / max(rate, 0.1)
            print(f"  {processed}/{total_points} ({processed*100//total_points}%) | "
                  f"{rate:.0f} pts/s | ETA: {eta:.0f}s", end="\r")

            if next_offset is None:
                break
            offset = next_offset

        elapsed = time.time() - t0
        print(f"\n  ✅ Indexed {processed} chunks in {elapsed:.1f}s")

    # ── Verification ──
    print(f"\n[Verify] Collection stats:")
    bm25_info = client.get_collection(BM25_COLLECTION)
    print(f"  BM25 collection: {bm25_info.points_count} points")

    # Verify source is untouched
    source_info = client.get_collection(source_collection)
    print(f"  Source collection: {source_info.points_count} points (should be {total_points})")
    assert source_info.points_count == total_points, "SOURCE COLLECTION MODIFIED!"

    # Test BM25 search
    print(f"\n[Verify] BM25 search: 'Do not freeze'")
    q = list(bm25.query_embed("Do not freeze"))[0]
    results = client.query_points(
        collection_name=BM25_COLLECTION,
        query=models.SparseVector(
            indices=q.indices.tolist(),
            values=q.values.tolist(),
        ),
        using="bm25",
        limit=5,
        with_payload=["text", "ref_id", "rt_id"],
    )
    for i, pt in enumerate(results.points, 1):
        text = pt.payload.get("text", "")[:80].replace("\n", " ")
        print(f"  #{i} score={pt.score:.4f} | rt={pt.payload.get('rt_id','')} | {pt.payload.get('ref_id','?')[:40]}")
        print(f"       \"{text}...\"")

    print(f"\n[Verify] BM25 search: 'discard unused portion'")
    q2 = list(bm25.query_embed("discard unused portion"))[0]
    results2 = client.query_points(
        collection_name=BM25_COLLECTION,
        query=models.SparseVector(indices=q2.indices.tolist(), values=q2.values.tolist()),
        using="bm25", limit=3,
        with_payload=["text", "ref_id"],
    )
    for i, pt in enumerate(results2.points, 1):
        text = pt.payload.get("text", "")[:80].replace("\n", " ")
        print(f"  #{i} score={pt.score:.4f} | {pt.payload.get('ref_id','?')[:40]}")

    print(f"\n[Verify] BM25 search: 'wash hands soap water'")
    q3 = list(bm25.query_embed("wash hands soap water"))[0]
    results3 = client.query_points(
        collection_name=BM25_COLLECTION,
        query=models.SparseVector(indices=q3.indices.tolist(), values=q3.values.tolist()),
        using="bm25", limit=3,
        with_payload=["text", "ref_id"],
    )
    for i, pt in enumerate(results3.points, 1):
        text = pt.payload.get("text", "")[:80].replace("\n", " ")
        print(f"  #{i} score={pt.score:.4f} | {pt.payload.get('ref_id','?')[:40]}")

    print(f"\n✅ DONE. Two-collection setup ready:")
    print(f"   Dense: {source_collection} (MedCPT, {total_points} points)")
    print(f"   BM25:  {BM25_COLLECTION} (sparse, {bm25_info.points_count} points)")


if __name__ == "__main__":
    main()
