"""Upload all embedded chunks to Qdrant Cloud.

Phase 1 of claim matching pipeline:
- Creates collection 'verifai_cidp' (768-dim, cosine)
- Uploads 4,776 embeddable chunks with full payload
- Creates payload indexes for rt_id, ref_id, ref_category filtering
- Idempotent: recreates collection on each run
"""
import os, sys, json, time, logging
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\revisto_evidence_aligned_clean")

from pathlib import Path
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models

load_dotenv(Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\.env"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
# Config
# ---------------------------------------------------------------
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION = "verifai_cidp"
VECTOR_DIM = 768
CHUNKS_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\chunks_final")
BATCH_SIZE = 100

# Payload fields to store (everything except the vector itself)
PAYLOAD_FIELDS = [
    "text", "ref_id", "sent_id", "section", "segment_type",
    "rt_id", "ref_category", "reference_type_name",
    "numeric_tokens", "doc_metadata", "chunk_index",
    "source_table_html", "approx_tokens", "embeddable",
]


def main():
    logger.info(f"Connecting to Qdrant: {QDRANT_URL}")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=60)

    # Check connectivity
    collections = client.get_collections().collections
    logger.info(f"Connected. Existing collections: {[c.name for c in collections]}")

    # Recreate collection
    existing = [c.name for c in collections]
    if COLLECTION in existing:
        logger.info(f"Deleting existing collection '{COLLECTION}'...")
        client.delete_collection(COLLECTION)
        time.sleep(2)

    logger.info(f"Creating collection '{COLLECTION}' (dim={VECTOR_DIM}, cosine)")
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=models.VectorParams(
            size=VECTOR_DIM,
            distance=models.Distance.COSINE,
        ),
    )

    # Create payload indexes for filtered search
    for field in ["rt_id", "ref_id", "ref_category", "segment_type"]:
        client.create_payload_index(
            collection_name=COLLECTION,
            field_name=field,
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
    logger.info("Payload indexes created: rt_id, ref_id, ref_category, segment_type")

    # ---------------------------------------------------------------
    # Upload chunks
    # ---------------------------------------------------------------
    files = sorted(CHUNKS_DIR.glob("*.chunks.json"))
    logger.info(f"Found {len(files)} chunk files")

    total_uploaded = 0
    total_skipped = 0
    point_id = 0
    batch_points = []
    start = time.time()

    for fi, jf in enumerate(files):
        data = json.loads(jf.read_text(encoding="utf-8"))

        for chunk in data:
            if not chunk.get("embeddable", False):
                total_skipped += 1
                continue

            vector = chunk.get("vector", [])
            if not vector or len(vector) != VECTOR_DIM:
                logger.warning(f"Chunk {chunk.get('sent_id')} has invalid vector (len={len(vector)})")
                total_skipped += 1
                continue

            # Build payload
            payload = {}
            for field in PAYLOAD_FIELDS:
                if field in chunk and chunk[field] is not None:
                    payload[field] = chunk[field]

            batch_points.append(models.PointStruct(
                id=point_id,
                vector=vector,
                payload=payload,
            ))
            point_id += 1

            # Flush batch
            if len(batch_points) >= BATCH_SIZE:
                client.upsert(
                    collection_name=COLLECTION,
                    points=batch_points,
                )
                total_uploaded += len(batch_points)
                batch_points = []

                elapsed = time.time() - start
                rate = total_uploaded / max(1, elapsed)
                logger.info(
                    f"[{fi+1}/{len(files)}] uploaded={total_uploaded} "
                    f"rate={rate:.0f} pts/s"
                )

    # Flush remaining
    if batch_points:
        client.upsert(
            collection_name=COLLECTION,
            points=batch_points,
        )
        total_uploaded += len(batch_points)

    elapsed = time.time() - start
    logger.info(f"\nUpload complete in {elapsed:.1f}s")
    logger.info(f"Uploaded: {total_uploaded}")
    logger.info(f"Skipped: {total_skipped}")

    # Verify
    info = client.get_collection(COLLECTION)
    logger.info(f"\nCollection '{COLLECTION}' stats:")
    logger.info(f"  Points: {info.points_count}")
    logger.info(f"  Status: {info.status}")


if __name__ == "__main__":
    main()
