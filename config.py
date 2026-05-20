"""Configuration for the MLR-compliant substantiation pipeline.

All settings are loaded from environment variables with sensible defaults.
Supports both Qdrant (vectors) and Elasticsearch (BM25 lexical) for hybrid search.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env from the new_pipeline directory
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path, override=True)


@dataclass
class LLMConfig:
    """LLM provider settings for classification, typization, cleaning, and judge."""

    # Claude (used for LLM Judge — highest quality reasoning)
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    judge_model: str = field(default_factory=lambda: os.getenv("JUDGE_MODEL", "claude-sonnet-4-6"))

    # OpenAI — GPT-5.5 for classification/typization, GPT-5.2 for cleaning
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    classifier_model: str = field(default_factory=lambda: os.getenv("CLASSIFIER_MODEL", "gpt-5.5"))
    cleaning_model: str = field(default_factory=lambda: os.getenv("CLEANING_MODEL", "gpt-5.2"))

    # Which provider to use for classification/typization
    classifier_provider: str = field(
        default_factory=lambda: os.getenv("CLASSIFIER_PROVIDER", "openai")  # "openai" or "anthropic"
    )


@dataclass
class EmbeddingConfig:
    """Embedding model settings — MedCPT asymmetric encoders."""

    # MedCPT uses separate encoders for articles (ingestion) and queries (search)
    article_model: str = field(
        default_factory=lambda: os.getenv("EMBED_MODEL", "ncbi/MedCPT-Article-Encoder")
    )
    query_model: str = field(
        default_factory=lambda: os.getenv("QUERY_EMBED_MODEL", "ncbi/MedCPT-Query-Encoder")
    )
    embedding_dim: int = 768
    device: str = field(default_factory=lambda: os.getenv("EMBED_DEVICE", "cpu"))
    hf_token: Optional[str] = field(default_factory=lambda: os.getenv("HF_TOKEN"))


@dataclass
class QdrantConfig:
    """Qdrant vector database settings."""
    url: str = field(default_factory=lambda: os.getenv("QDRANT_URL", "http://localhost:6333"))
    api_key: Optional[str] = field(default_factory=lambda: os.getenv("QDRANT_API_KEY") or None)
    collection_name: str = field(default_factory=lambda: os.getenv("QDRANT_COLLECTION", "verifai_mlr"))
    # Vector params
    vector_size: int = 768  # MedCPT output dimension
    distance: str = "Cosine"


@dataclass
class ElasticsearchConfig:
    """Elasticsearch settings — used for BM25 lexical search in hybrid mode."""
    url: str = field(default_factory=lambda: os.getenv("ES_URL", "http://localhost:9200"))
    user: str = field(default_factory=lambda: os.getenv("ES_USER", "elastic"))
    password: str = field(default_factory=lambda: os.getenv("ES_PASS", ""))
    api_key: Optional[str] = field(default_factory=lambda: os.getenv("API_KEY"))
    index_name: str = field(default_factory=lambda: os.getenv("ES_INDEX", "verifai_mlr_index"))
    verify_certs: bool = field(
        default_factory=lambda: os.getenv("ES_VERIFY_CERTS", "false").lower() == "true"
    )


@dataclass
class IngestionConfig:
    """Settings for the ingestion phase."""
    landingai_api_key: str = field(default_factory=lambda: os.getenv("LANDINGAI_API_KEY", ""))
    min_chunk_length: int = 5
    segmentation_level: str = "sentence"  # "sentence" or "block"
    batch_size: int = 500
    cache_dir: Optional[str] = field(default_factory=lambda: os.getenv("PARSE_CACHE_DIR"))


@dataclass
class RetrievalConfig:
    """Settings for the hybrid retrieval phase."""
    # Score weights for hybrid search (Qdrant vectors + ES BM25)
    lexical_weight: float = 0.3   # BM25 from Elasticsearch
    semantic_weight: float = 0.7  # Cosine from Qdrant

    # Tier boost multipliers applied to Qdrant scores
    tier_p_boost: float = 2.0   # Primary sources
    tier_a_boost: float = 1.0   # Acceptable sources
    tier_c_boost: float = 0.5   # Conditional sources
    # Tier N = hard filter (excluded from results)

    # Retrieval settings
    initial_candidates: int = 50   # How many to retrieve before re-ranking
    rerank_topk: int = 10          # How many to keep after cross-encoder
    final_topk: int = 5            # How many to send to the LLM Judge


@dataclass
class EvaluationConfig:
    """Settings for the evaluation phase (Substantiation Judge)."""
    # Coverage score thresholds (from Section 3.3 of requirements)
    pass_threshold: float = 80.0
    soft_flag_threshold: float = 60.0  # Below this = BLOCK

    # Rounding tolerance for numeric claims (Section 4.2)
    rounding_tolerance_pct: float = 2.0
    rounding_justification_pct: float = 5.0

    # Fair balance enforcement (Section 8.4)
    enforce_fair_balance: bool = True


@dataclass
class PipelineConfig:
    """Top-level configuration container."""
    llm: LLMConfig = field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    qdrant: QdrantConfig = field(default_factory=QdrantConfig)
    elasticsearch: ElasticsearchConfig = field(default_factory=ElasticsearchConfig)
    ingestion: IngestionConfig = field(default_factory=IngestionConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)

    # Paths to the categorization MD files (used as LLM prompt context)
    categorization_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("CATEGORIZATION_DIR", str(Path(__file__).parent / "categorization"))
        )
    )

    @property
    def claim_classification_path(self) -> Path:
        return self.categorization_dir / "Claim_classification.md"

    @property
    def reference_types_path(self) -> Path:
        return self.categorization_dir / "Reference_Document_Types.md"

    @property
    def claim_mapping_path(self) -> Path:
        return self.categorization_dir / "Claim-to-Reference_Mapping.md"

    @property
    def substantiation_requirements_path(self) -> Path:
        return self.categorization_dir / "Claim_Substantiation_Requirements_v1_1.md"


def load_config() -> PipelineConfig:
    """Load pipeline configuration from environment variables."""
    return PipelineConfig()
