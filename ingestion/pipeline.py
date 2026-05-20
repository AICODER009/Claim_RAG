"""Ingestion Pipeline Orchestrator — chains all ingestion steps.

This is the main entry point for Stage 1 of the pipeline.
For each PDF:
  1. Parse PDF via LandingAI ADE (layout-aware, with table/figure detection)
  2. Extract bibliographic metadata (GPT-5.2 reads first page → authors, DOI, etc.)
  3. Typize document (GPT-5.5 assigns RT-ID from first pages)
  4. Process chunks by type:
     - Text → PySBD sentence splitting
     - Tables → GPT-5.2 linearizes into declarative statements (one per row)
     - Figures → GPT-5.2 extracts factual claims from descriptions
  5. Normalize text (Unicode + contextualized numeric extraction)
  6. Embed chunks (MedCPT Article Encoder)
  7. Store in Qdrant with full MLR metadata (rt_id, doc_metadata, numeric_contexts)

Usage:
    from new_pipeline.ingestion.pipeline import IngestionPipeline
    from new_pipeline.config import load_config
    
    config = load_config()
    pipeline = IngestionPipeline(config)
    stats = await pipeline.ingest_pdf(Path("reference.pdf"), org_id=1, brand_id=1)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from qdrant_client import QdrantClient, models

from ..config import PipelineConfig
from .chunker import get_chunker
from .content_cleaner import ContentCleaner
from .embedder import MedCPTEmbedder
from .metadata_extractor import MetadataExtractor
from .normalizer import normalize_unicode, extract_numeric_strings, extract_numeric_contexts
from .pdf_parser import LandingAIPDFParser, ParsedChunk
from .typizer import Typizer

logger = logging.getLogger(__name__)

# Default cache directory (inside new_pipeline)
_DEFAULT_CACHE_DIR = Path(__file__).parent.parent / "cache" / "parsed_pdfs"


class IngestionPipeline:
    """End-to-end ingestion pipeline for reference documents."""

    def __init__(self, config: PipelineConfig):
        self.config = config

        logger.info("Initializing ingestion pipeline components...")

        # Resolve cache_dir: use config, or default inside new_pipeline/cache/
        cache_dir = (
            Path(config.ingestion.cache_dir)
            if config.ingestion.cache_dir
            else _DEFAULT_CACHE_DIR
        )

        # 1. PDF Parser (LandingAI ADE)
        self._parser = LandingAIPDFParser(
            api_key=config.ingestion.landingai_api_key,
            cache_dir=cache_dir,
        )

        # 2. Metadata Extractor (GPT-5.2 → authors, DOI, journal, year)
        self._metadata_extractor = MetadataExtractor(
            api_key=config.llm.openai_api_key,
            model=config.llm.cleaning_model,  # GPT-5.2
        )

        # 3. Sentence chunker (PySBD — only for text chunks)
        self._chunker = get_chunker(config.ingestion.segmentation_level)

        # 4. Content cleaner (GPT-5.2 — tables/figures linearization)
        self._cleaner = ContentCleaner(
            api_key=config.llm.openai_api_key,
            model=config.llm.cleaning_model,
        )

        # 5. Embedder (MedCPT Article Encoder)
        self._embedder = MedCPTEmbedder(
            article_model_name=config.embedding.article_model,
            query_model_name=config.embedding.query_model,
            device=config.embedding.device,
            hf_token=config.embedding.hf_token,
        )

        # 6. Typizer (GPT-5.5 assigns RT-ID)
        self._typizer = Typizer(
            provider=config.llm.classifier_provider,
            model=config.llm.classifier_model,
            api_key=(
                config.llm.openai_api_key
                if config.llm.classifier_provider == "openai"
                else config.llm.anthropic_api_key
            ),
            taxonomy_path=config.reference_types_path,
        )

        # 7. Qdrant client
        self._qdrant = QdrantClient(
            url=config.qdrant.url,
            api_key=config.qdrant.api_key,
        )

        self._ensure_collection()
        logger.info("Ingestion pipeline ready")

    def _ensure_collection(self) -> None:
        """Create Qdrant collection if it doesn't exist."""
        collections = self._qdrant.get_collections().collections
        existing_names = {c.name for c in collections}

        if self.config.qdrant.collection_name not in existing_names:
            self._qdrant.create_collection(
                collection_name=self.config.qdrant.collection_name,
                vectors_config=models.VectorParams(
                    size=self.config.qdrant.vector_size,
                    distance=models.Distance.COSINE,
                ),
            )
            # Create payload indexes for filtering
            for field_name in ["rt_id", "ref_id", "org_id", "brand_id", "segment_type"]:
                self._qdrant.create_payload_index(
                    collection_name=self.config.qdrant.collection_name,
                    field_name=field_name,
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )
            logger.info(f"Created Qdrant collection: {self.config.qdrant.collection_name}")
        else:
            logger.info(f"Qdrant collection exists: {self.config.qdrant.collection_name}")

    async def ingest_pdf(
        self,
        pdf_path: Path,
        org_id: int,
        brand_id: int,
    ) -> Dict[str, Any]:
        """Ingest a single PDF through the full pipeline.

        Args:
            pdf_path: Path to the reference PDF.
            org_id: Organization ID for multi-tenancy.
            brand_id: Brand ID for multi-tenancy.

        Returns:
            Dict with ingestion statistics.
        """
        logger.info(f"▶ Ingesting: {pdf_path.name}")
        stats = {"file": pdf_path.name, "chunks": 0, "errors": 0}

        # ---------------------------------------------------------------
        # Step 1: Parse PDF via LandingAI ADE
        # ---------------------------------------------------------------
        parse_result = await self._parser.parse(pdf_path)
        if not parse_result.chunks:
            logger.error(f"  ✗ No chunks extracted from: {pdf_path.name}")
            stats["errors"] += 1
            return stats

        text_count = sum(1 for c in parse_result.chunks if c.chunk_type == "text")
        table_count = sum(1 for c in parse_result.chunks if c.chunk_type == "table")
        figure_count = sum(1 for c in parse_result.chunks if c.chunk_type == "figure")
        logger.info(
            f"  ✓ Parsed: {len(parse_result.chunks)} chunks "
            f"({text_count} text, {table_count} table, {figure_count} figure)"
        )

        # ---------------------------------------------------------------
        # Step 2: Extract bibliographic metadata (GPT-5.2)
        # ---------------------------------------------------------------
        doc_metadata = await self._metadata_extractor.extract(
            parse_result.markdown, max_words=400
        )
        doc_title = doc_metadata.get("title", pdf_path.stem)
        logger.info(f"  ✓ Metadata: '{doc_title[:60]}' by {doc_metadata.get('authors', ['?'])[0] if doc_metadata.get('authors') else '?'}")

        # ---------------------------------------------------------------
        # Step 3: Typize document (GPT-5.5 assigns RT-ID)
        # ---------------------------------------------------------------
        first_page_text = "\n".join(
            c.text for c in parse_result.chunks
            if c.chunk_type == "text" and c.page <= 2
        )[:8000]
        typization = self._typizer.classify(first_page_text, filename=pdf_path.name)
        logger.info(f"  ✓ Typized as {typization.rt_id} ({typization.reference_type_name})")

        # ---------------------------------------------------------------
        # Step 4-6: Process each chunk → clean/split → normalize → embed
        # ---------------------------------------------------------------
        points_to_upsert = []
        ref_id = pdf_path.stem
        sent_counter = 0

        for chunk in parse_result.chunks:
            try:
                chunk_segments = self._process_chunk(chunk)

                for segment_text, segment_type, source_label in chunk_segments:
                    sent_counter += 1

                    # Normalize text (Unicode NFKC + whitespace)
                    clean_text = normalize_unicode(segment_text)
                    if len(clean_text) < self.config.ingestion.min_chunk_length:
                        continue

                    # Extract contextualized numeric tokens (Section 4)
                    numeric_tokens = extract_numeric_strings(clean_text)
                    numeric_contexts = extract_numeric_contexts(clean_text)

                    # Generate MedCPT embedding
                    embedding = self._embedder.encode_article(clean_text)

                    # Build Qdrant point with COMPLETE payload
                    payload = {
                        # Chunk identification
                        "ref_id": ref_id,
                        "ref_title": doc_title,
                        "sent_id": f"{ref_id}::page{chunk.page}::sent{sent_counter}",
                        "text": clean_text,
                        "page": chunk.page + 1,  # Convert to 1-indexed
                        "sentence_number": sent_counter,
                        "segment_type": segment_type,
                        "source": source_label,

                        # Bounding box for visual grounding (Section 8.1)
                        "bbox": {
                            "x0": chunk.bbox[0], "y0": chunk.bbox[1],
                            "x1": chunk.bbox[2], "y1": chunk.bbox[3],
                        } if chunk.bbox else None,

                        # MLR metadata — THE KEY FIELDS
                        "rt_id": typization.rt_id,
                        "ref_category": typization.category.value,
                        "reference_type_name": typization.reference_type_name,

                        # Numeric tokens WITH context (Section 4)
                        "numeric_tokens": numeric_tokens,
                        "numeric_contexts": numeric_contexts,

                        # Bibliographic metadata (Section 8.1 audit trail)
                        "doc_metadata": doc_metadata,

                        # Multi-tenancy
                        "org_id": org_id,
                        "brand_id": brand_id,

                        "timestamp": datetime.utcnow().isoformat(),
                    }

                    points_to_upsert.append(
                        models.PointStruct(
                            id=str(uuid.uuid4()),
                            vector=embedding.tolist(),
                            payload=payload,
                        )
                    )

            except Exception as e:
                logger.error(f"  ✗ Error processing chunk on page {chunk.page}: {e}")
                stats["errors"] += 1

        # ---------------------------------------------------------------
        # Step 7: Batch upsert to Qdrant
        # ---------------------------------------------------------------
        if points_to_upsert:
            batch_size = self.config.ingestion.batch_size
            for i in range(0, len(points_to_upsert), batch_size):
                batch = points_to_upsert[i : i + batch_size]
                self._qdrant.upsert(
                    collection_name=self.config.qdrant.collection_name,
                    points=batch,
                )
            logger.info(f"  ✓ Indexed {len(points_to_upsert)} chunks to Qdrant")

        stats["chunks"] = len(points_to_upsert)
        stats["rt_id"] = typization.rt_id
        stats["reference_type"] = typization.reference_type_name
        stats["doc_title"] = doc_title
        logger.info(f"  ✓ Complete: {stats}")
        return stats

    def _process_chunk(
        self, chunk: ParsedChunk
    ) -> List[tuple[str, str, str | None]]:
        """Process a single LandingAI chunk into indexable segments.

        Different processing per chunk type:
        - text → PySBD sentence splitting
        - table → GPT-5.2 linearizes each row into a declarative statement
        - figure → GPT-5.2 extracts factual claims from the description

        Returns:
            List of (text, segment_type, source_label) tuples.
        """
        if chunk.chunk_type == "text":
            # Split text paragraphs into individual sentences
            sentences = self._chunker.split(chunk.text)
            return [(s, "text", None) for s in sentences]

        elif chunk.chunk_type == "table":
            # Tables: GPT-5.2 converts raw markdown into natural language
            # statements (one per row) for proper MedCPT embedding
            statements = self._cleaner.clean_table(chunk.text)
            page_label = f"Table on page {chunk.page + 1}"
            return [
                (stmt, "table_row", f"{page_label}; row {i + 1}")
                for i, stmt in enumerate(statements)
            ]

        elif chunk.chunk_type == "figure":
            # Figures: GPT-5.2 extracts factual claims from description
            claims = self._cleaner.clean_figure(chunk.text)
            page_label = f"Figure on page {chunk.page + 1}"
            return [
                (claim, "figure", page_label)
                for claim in claims
            ]

        else:
            # Unknown type: treat as text
            return [(chunk.text, chunk.chunk_type, None)]

    async def ingest_directory(
        self,
        directory: Path,
        org_id: int,
        brand_id: int,
    ) -> List[Dict[str, Any]]:
        """Ingest all PDFs in a directory.

        Args:
            directory: Path containing PDFs.
            org_id: Organization ID.
            brand_id: Brand ID.

        Returns:
            List of stats dicts, one per PDF.
        """
        pdf_files = sorted(directory.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDFs in {directory}")

        all_stats = []
        for pdf_path in pdf_files:
            try:
                stats = await self.ingest_pdf(pdf_path, org_id, brand_id)
                all_stats.append(stats)
            except Exception as e:
                logger.error(f"Failed to ingest {pdf_path.name}: {e}")
                all_stats.append({
                    "file": pdf_path.name, "chunks": 0,
                    "errors": 1, "error": str(e),
                })

        total_chunks = sum(s["chunks"] for s in all_stats)
        total_errors = sum(s["errors"] for s in all_stats)
        logger.info(
            f"Ingestion complete: {len(pdf_files)} PDFs, "
            f"{total_chunks} chunks, {total_errors} errors"
        )
        return all_stats
