"""Upload embedded chunks to Qdrant Cloud.

Option 1: Each embeddable chunk gets a full payload including:
  - All chunk fields (text, section, segment_type, etc.)
  - doc_metadata (title, authors, journal, year, DOI)
  - doc_references: all bibliography entries from the same document
    bundled as a list for in-text citation resolution

Non-embeddable chunks (references, figures) are NOT uploaded as points
but their reference text IS bundled into the embeddable chunks' payload.
"""
import os, sys, json, time, logging, uuid
sys.path.insert(0, r"D:\pip_libs")  # qdrant-client installed here (C: full)
from pathlib import Path

# Load .env
from dotenv import load_dotenv
load_dotenv(Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\.env"))

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from qdrant_client import QdrantClient, models

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\chunks_final")
COLLECTION = os.getenv("QDRANT_COLLECTION", "verifai_mlr")
VECTOR_DIM = 768


def build_doc_references(all_chunks: list[dict]) -> list[dict]:
    """Extract reference chunks from a document into a compact list.
    
    Returns list of {"index": 1, "text": "Van den Bergh PY..."} entries
    for in-text citation resolution by the Judge.
    """
    refs = []
    for c in all_chunks:
        if c["segment_type"] == "reference":
            text = c["text"].strip()
            # Try to extract reference number
            import re
            num_match = re.match(r"^(\d+)\.\s+", text)
            ref_idx = int(num_match.group(1)) if num_match else len(refs) + 1
            refs.append({
                "index": ref_idx,
                "text": text[:500],  # Cap at 500 chars to limit payload size
            })
    return refs


def main():
    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")
    
    if not url or not api_key:
        logger.error("QDRANT_URL or QDRANT_API_KEY not set")
        sys.exit(1)
    
    # Strip quotes if present
    url = url.strip('"').strip("'")
    api_key = api_key.strip('"').strip("'")
    
    logger.info(f"Connecting to Qdrant: {url[:50]}...")
    client = QdrantClient(url=url, api_key=api_key, timeout=60)
    
    # Check if collection exists
    collections = [c.name for c in client.get_collections().collections]
    
    if COLLECTION in collections:
        info = client.get_collection(COLLECTION)
        logger.info(f"Collection '{COLLECTION}' exists: {info.points_count} points")
        logger.info("Recreating collection for fresh upload...")
        client.delete_collection(COLLECTION)
    
    # Create collection with cosine distance (MedCPT vectors are not pre-normalized)
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=models.VectorParams(
            size=VECTOR_DIM,
            distance=models.Distance.COSINE,
        ),
    )
    logger.info(f"Created collection '{COLLECTION}' (dim={VECTOR_DIM}, cosine)")
    
    # Create payload indexes for filtering
    for field, schema in [
        ("rt_id", models.PayloadSchemaType.KEYWORD),
        ("ref_id", models.PayloadSchemaType.KEYWORD),
        ("ref_category", models.PayloadSchemaType.KEYWORD),
        ("segment_type", models.PayloadSchemaType.KEYWORD),
        ("sent_id", models.PayloadSchemaType.KEYWORD),
    ]:
        client.create_payload_index(
            collection_name=COLLECTION,
            field_name=field,
            field_schema=schema,
        )
    logger.info("Payload indexes created (rt_id, ref_id, ref_category, segment_type, sent_id)")
    
    # Upload files
    files = sorted(OUT_DIR.glob("*.chunks.json"))
    logger.info(f"Found {len(files)} chunk files")
    
    total_uploaded = 0
    total_skipped = 0
    batch_points = []
    BATCH_SIZE = 100
    start = time.time()
    
    for fi, jf in enumerate(files):
        all_chunks = json.loads(jf.read_text(encoding="utf-8"))
        stem = jf.stem.replace(".chunks", "")
        
        # Build document-level reference list (Option 1)
        doc_refs = build_doc_references(all_chunks)
        
        # Get doc metadata from first chunk
        doc_meta = all_chunks[0].get("doc_metadata", {}) if all_chunks else {}
        
        for c in all_chunks:
            if not c.get("embeddable", False):
                total_skipped += 1
                continue
            
            vec = c.get("vector", [])
            if not vec or len(vec) != VECTOR_DIM:
                logger.warning(f"Bad vector in {stem}::chunk-{c['chunk_index']}")
                total_skipped += 1
                continue
            
            # Build payload (everything except the vector itself)
            payload = {
                "text": c["text"],
                "section": c.get("section", ""),
                "segment_type": c["segment_type"],
                "chunk_index": c["chunk_index"],
                "approx_tokens": c.get("approx_tokens", 0),
                "source_table_html": c.get("source_table_html", ""),
                "numeric_tokens": c.get("numeric_tokens", []),
                # Document-level fields
                "sent_id": c.get("sent_id", ""),
                "ref_id": c.get("ref_id", ""),
                "rt_id": c.get("rt_id", ""),
                "ref_category": c.get("ref_category", ""),
                "reference_type_name": c.get("reference_type_name", ""),
                # Document metadata for citation
                "doc_metadata": doc_meta,
                # Document bibliography for in-text citation resolution
                "doc_references": doc_refs,
                # Source file for debugging
                "source_file": stem,
            }
            
            # Generate deterministic UUID from sent_id + chunk_index
            point_id = str(uuid.uuid5(
                uuid.NAMESPACE_DNS,
                f"{c.get('sent_id', stem)}::{c['chunk_index']}"
            ))
            
            batch_points.append(models.PointStruct(
                id=point_id,
                vector=vec,
                payload=payload,
            ))
            
            # Upload batch
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
                    f"rate={rate:.1f} pts/s"
                )
    
    # Upload remaining batch
    if batch_points:
        client.upsert(
            collection_name=COLLECTION,
            points=batch_points,
        )
        total_uploaded += len(batch_points)
    
    elapsed = time.time() - start
    
    # Verify
    info = client.get_collection(COLLECTION)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"QDRANT UPLOAD COMPLETE")
    logger.info(f"{'='*60}")
    logger.info(f"Collection: {COLLECTION}")
    logger.info(f"Points uploaded: {total_uploaded}")
    logger.info(f"Points in Qdrant: {info.points_count}")
    logger.info(f"Skipped (non-embeddable): {total_skipped}")
    logger.info(f"Time: {elapsed:.1f}s")
    logger.info(f"Payload indexes: rt_id, ref_id, ref_category, segment_type, sent_id")
    logger.info(f"Each point carries doc_references for citation resolution")
    
    if info.points_count == total_uploaded:
        logger.info("VERIFIED: Point count matches upload count")
    else:
        logger.warning(f"MISMATCH: uploaded {total_uploaded} but Qdrant has {info.points_count}")


if __name__ == "__main__":
    main()
