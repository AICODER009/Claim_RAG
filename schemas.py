"""Pydantic schemas for the MLR-compliant substantiation pipeline.

Defines data models for:
- Reference Document Typization (RT-IDs)
- Claim Classification (CT-IDs)
- PICOT decomposition
- Coverage scoring
- Audit trail records
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Reference Document Types (from Reference_Document_Types.md)
# ---------------------------------------------------------------------------

class ReferenceCategory(str, Enum):
    """Top-level reference categories (B1–B9)."""
    B1 = "B1"  # Regulatory / Approved Labeling
    B2 = "B2"  # Clinical Trial Evidence
    B3 = "B3"  # Peer-Reviewed Literature
    B4 = "B4"  # Conference / Congress Materials
    B5 = "B5"  # Real-World / Health-Economics Evidence
    B6 = "B6"  # Preclinical / Nonclinical
    B7 = "B7"  # Regulatory Agency Communications
    B8 = "B8"  # Educational / Disease-Awareness
    B9 = "B9"  # Internal / Other


class ReferenceTypization(BaseModel):
    """Result of LLM typization during ingestion (Stage 1)."""
    rt_id: str = Field(..., description="Reference type ID, e.g. RT-101")
    category: ReferenceCategory = Field(..., description="Top-level category, e.g. B1")
    reference_type_name: str = Field(..., description="Human-readable name, e.g. 'US Prescribing Information (USPI)'")
    confidence: float = Field(ge=0.0, le=1.0, description="LLM classification confidence")


# ---------------------------------------------------------------------------
# Claim Classification (from Claim_classification.md)
# ---------------------------------------------------------------------------

class ClaimClassification(BaseModel):
    """Result of LLM claim classification (Stage 2 / Step 1)."""
    ct_id: str = Field(..., description="Primary claim type ID, e.g. CT-201")
    claim_type_name: str = Field(..., description="Human-readable name, e.g. 'Primary-endpoint efficacy'")
    secondary_ct_id: Optional[str] = Field(None, description="A10 secondary tag, e.g. CT-A01 for RWE")
    confidence: float = Field(ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# PICOT Decomposition
# ---------------------------------------------------------------------------

class PICOTComponents(BaseModel):
    """PICOT decomposition of a claim (Section 2.3 of Substantiation Requirements)."""
    population: Optional[str] = Field(None, description="Target population, e.g. 'Adults with T2DM'")
    intervention: Optional[str] = Field(None, description="Drug + dose, e.g. 'Cytisinicline 1.5mg'")
    comparator: Optional[str] = Field(None, description="Comparator, e.g. 'Placebo'")
    outcome: Optional[str] = Field(None, description="Clinical endpoint, e.g. 'Continuous abstinence'")
    timeframe: Optional[str] = Field(None, description="Assessment window, e.g. 'Weeks 9-24'")


# ---------------------------------------------------------------------------
# Tier System (from Claim-to-Reference_Mapping.md)
# ---------------------------------------------------------------------------

class EvidenceTier(str, Enum):
    """Evidence acceptability tier for a given CT→RT mapping."""
    PRIMARY = "P"       # Primary / preferred source
    ACCEPTABLE = "A"    # Acceptable alternative
    CONDITIONAL = "C"   # Conditional — requires qualification
    NOT_ACCEPTABLE = "N"  # Not acceptable for this claim type


class TierMapping(BaseModel):
    """Single entry from the CT→RT mapping matrix."""
    rt_id: str
    tier: EvidenceTier
    note: Optional[str] = None


# ---------------------------------------------------------------------------
# Coverage Score (Section 3 of Substantiation Requirements)
# ---------------------------------------------------------------------------

class SubAssertionResult(BaseModel):
    """Coverage result for a single sub-assertion within a claim."""
    sub_assertion: str = Field(..., description="The distinct factual element, e.g. '32.6% abstinence rate'")
    is_covered: bool = Field(..., description="Whether this element is present in the retrieved evidence")
    source_rt_id: Optional[str] = Field(None, description="RT-ID of the document that covers this element")
    source_sent_id: Optional[str] = Field(None, description="Specific sentence/chunk ID")
    verbatim_anchor: Optional[str] = Field(None, description="Exact text from the source that proves this element")


class CoverageResult(BaseModel):
    """Per-claim coverage score (Section 3.1)."""
    claim_text: str
    sub_assertions: List[SubAssertionResult]
    coverage_score: float = Field(ge=0.0, le=100.0, description="0-100 coverage percentage")
    picot: PICOTComponents
    picot_alignment: Dict[str, bool] = Field(
        default_factory=dict,
        description="Per-dimension PICOT alignment: {'population': True, 'timeframe': False, ...}"
    )


class CoverageVerdict(str, Enum):
    """Final verdict based on coverage score thresholds (Section 3.3)."""
    PASS = "pass"           # Score >= 80
    SOFT_FLAG = "soft_flag"  # Score 60-79
    BLOCK = "block"          # Score < 60


# ---------------------------------------------------------------------------
# Audit Trail (Section 8 of Substantiation Requirements)
# ---------------------------------------------------------------------------

class CitationMetadata(BaseModel):
    """Mandatory + conditional citation fields per Section 8.1."""
    # Mandatory fields (all source types)
    full_citation: str = Field(..., description="Author, title, source, year")
    file_name: str = Field(..., description="Exact PDF filename in reference library")
    page_number: int = Field(..., description="Page where evidence was found")
    verbatim_anchor_text: str = Field(..., description="Exact text that proves the claim")

    # Conditional fields (depend on document type)
    doi: Optional[str] = None
    volume: Optional[str] = None
    page_range: Optional[str] = None
    section_heading: Optional[str] = None
    sentence_index: Optional[int] = None
    table_figure_number: Optional[str] = None
    data_on_file_label: Optional[bool] = Field(None, description="Required for CSR documents")
    preliminary_data_flag: Optional[bool] = Field(None, description="Required for conference posters")


class AuditRecord(BaseModel):
    """Immutable audit trail entry for a single claim substantiation."""
    claim_text: str
    claim_ct_id: str
    classification: ClaimClassification
    picot: PICOTComponents

    # Retrieved evidence
    retrieved_citations: List[CitationMetadata]
    evidence_rt_ids: List[str] = Field(..., description="RT-IDs of all retrieved documents")

    # Evaluation results
    coverage_result: CoverageResult
    verdict: CoverageVerdict
    fair_balance_linked: bool = Field(..., description="Whether safety info was found for efficacy claims")
    secondary_citation_flag: bool = Field(False, description="True if evidence relies on a secondary citation")

    # Governance
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    reviewer_notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Ingestion Document (what gets stored in vector DB)
# ---------------------------------------------------------------------------

class IndexedChunk(BaseModel):
    """A single chunk stored in the vector database during ingestion."""
    ref_id: str
    ref_title: str
    sent_id: str
    text: str
    section: Optional[str] = None
    page: int
    paragraph_number: int
    sentence_number: int
    bbox: Optional[Dict[str, float]] = None
    segment_type: str  # text, table_row, table_cell, figure
    source: Optional[str] = None  # "Table 2; row 3" or "Figure 1"

    # Embeddings
    vector: List[float] = Field(..., description="MedCPT article embedding")

    # Numeric features (kept for Section 4 compliance)
    numeric_tokens: List[str] = Field(default_factory=list)

    # NEW: Reference Typization metadata
    rt_id: str = Field(..., description="Reference type ID assigned during ingestion")
    ref_category: ReferenceCategory = Field(..., description="Top-level category B1-B9")

    # Bibliographic metadata
    doc_metadata: Optional[Dict[str, Any]] = None

    # Multi-tenancy
    org_id: int
    brand_id: int

    timestamp: datetime = Field(default_factory=datetime.utcnow)
