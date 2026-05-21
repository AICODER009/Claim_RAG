"""Pydantic schemas for the MLR-compliant substantiation pipeline.

Defines data models for:
- Reference Document Typization (RT-IDs)
- Claim Classification (CT-IDs)
- PICOT decomposition
- Coverage scoring
- Audit trail records

Updated to align with categorization_new/ (pre-2026-05-20):
  - ClaimGroup: A10 = Off-Label/Scientific-Exchange, A11 = Study Design/Methodology
  - New CT-D01–CT-D06 claim types (Study Design, no reference mapping yet)
  - AudienceConstraint: payer-only, HCP-only per Claim Attributes sheet
  - Deprecated: RT-602 (merged into RT-601)
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
# Claim Group (top-level taxonomy sections, updated categorization_new)
# ---------------------------------------------------------------------------

class ClaimGroup(str, Enum):
    """Top-level claim group A1–A11 (from Claim_classification_2.md).

    NOTE: A10 and A11 meaning changed vs. old taxonomy:
      Old A10 = Evidence-Type modifiers (CT-A0x)  → now modifier-only rows in Claim Attributes
      Old A11 = Off-Label / Scientific-Exchange   → NOW A10
      New A11 = Study Design / Methodology        → BRAND NEW (CT-D01–CT-D06, origin 2026-05-08)
    """
    A1  = "A1"   # Indication & Regulatory
    A2  = "A2"   # Efficacy
    A3  = "A3"   # Safety & Tolerability
    A4  = "A4"   # Comparative
    A5  = "A5"   # Pharmacology / MoA
    A6  = "A6"   # Dosing, Administration & Handling
    A7  = "A7"   # Disease-State / Epidemiology
    A8  = "A8"   # Patient-Centric
    A9  = "A9"   # Economic / HCEI
    A10 = "A10"  # Off-Label / Scientific-Exchange  (CT-B01–CT-B04; was A11)
    A11 = "A11"  # Study Design / Methodology       (CT-D01–CT-D06; NEW)
    # A10 Evidence-type modifiers (CT-A01–CT-A08) no longer have a group label;
    # they are flagged via MappingMatrix.MODIFIER_CT_IDS and the Claim Attributes sheet.


# ---------------------------------------------------------------------------
# Audience Constraint (from Claim Attributes sheet)
# ---------------------------------------------------------------------------

class AudienceConstraint(str, Enum):
    """Audience restriction for a claim type, per Claim Attributes sheet."""
    UNRESTRICTED = "unrestricted"   # HCP + patient + payer
    HCP_ONLY     = "hcp_only"       # CT-B01 (SIUU), CT-B04 (scientific-exchange)
    PAYER_ONLY   = "payer_only"     # CT-405, CT-901–CT-909, CT-B02, CT-B03


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
    B6 = "B6"  # Periodic Safety / Pharmacovigilance  (NOTE: B6 corrected from old label)
    B7 = "B7"  # Regulatory Agency Communications
    B8 = "B8"  # Instruments, Standards & Scientific Documents
    B9 = "B9"  # Internal / Other


class ReferenceTypization(BaseModel):
    """Result of LLM typization during ingestion (Stage 1)."""
    rt_id: str = Field(..., description="Reference type ID, e.g. RT-101")
    category: ReferenceCategory = Field(..., description="Top-level category, e.g. B1")
    reference_type_name: str = Field(..., description="Human-readable name, e.g. 'US Prescribing Information (USPI)'")
    confidence: float = Field(ge=0.0, le=1.0, description="LLM classification confidence")
    deprecated: bool = Field(False, description="True if this RT-ID is deprecated (e.g. RT-602 → RT-601)")


# ---------------------------------------------------------------------------
# Claim Classification (from Claim_classification_2.md)
# ---------------------------------------------------------------------------

class ClaimClassification(BaseModel):
    """Result of LLM claim classification (Stage 2 / Step 1).

    CT-ID taxonomy (categorization_new, pre-2026-05-20):
      A1:  CT-101–CT-110  Indication & Regulatory
      A2:  CT-201–CT-209  Efficacy
      A3:  CT-301–CT-311  Safety & Tolerability  (includes CT-311 Pregnancy)
      A4:  CT-401–CT-409  Comparative
      A5:  CT-501–CT-507  Pharmacology / MoA
      A6:  CT-601–CT-608  Dosing, Administration & Handling
      A7:  CT-701–CT-706  Disease-State / Epidemiology
      A8:  CT-801–CT-807  Patient-Centric
      A9:  CT-901–CT-909  Economic / HCEI  (payer audience only)
      A10: CT-B01–CT-B04  Off-Label / Scientific-Exchange  [was A11]
      A10 modifiers: CT-A01–CT-A08  Evidence-Type (must pair with primary CT)
      A11: CT-D01–CT-D06  Study Design / Methodology  [NEW, no mapping yet]
    """
    ct_id: str = Field(..., description="Primary claim type ID, e.g. CT-201 or CT-D01")
    claim_type_name: str = Field(..., description="Human-readable name, e.g. 'Primary-endpoint efficacy'")
    claim_group: Optional[str] = Field(
        None,
        description="Claim group code A1–A11, e.g. 'A2'. Populated from Claim Attributes."
    )
    secondary_ct_id: Optional[str] = Field(
        None,
        description=(
            "Secondary CT-ID for evidence-type modifier tags (CT-A01–CT-A08 from A10). "
            "Example: CT-A01 (RWE modifier) paired with CT-201 (primary efficacy). "
            "MUST NOT be a CT-D type — study-design claims use ct_id directly."
        ),
    )
    audience_constraint: AudienceConstraint = Field(
        AudienceConstraint.UNRESTRICTED,
        description="Audience restriction per Claim Attributes sheet."
    )
    is_modifier_only: bool = Field(
        False,
        description="True if ct_id is a modifier tag (CT-A01–CT-A08, CT-204) — must be paired."
    )
    is_study_design: bool = Field(
        False,
        description="True if ct_id is a Study Design claim (CT-D01–CT-D06, A11). "
                    "Reference mapping pending; engine returns a warning, not empty."
    )
    mapping_pending: bool = Field(
        False,
        description="True if ct_id has no reference mapping yet (CT-D01–CT-D06)."
    )
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
