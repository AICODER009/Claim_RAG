# New Pipeline — Implementation Plan

## Goal
Build a new MLR-compliant substantiation pipeline from scratch in `D:\revisto_evidence_aligned_clean\new_pipeline\`.
This pipeline implements the 6-step Claim-Type-Driven architecture shown in the PIPELINE_DESIGN diagram.

---

## Folder Structure

```
new_pipeline/
├── __init__.py
├── config.py                 # All settings, env vars, model paths
├── schemas.py                # Pydantic models for CT-ID, RT-ID, PICOT, CoverageScore, AuditRecord
│
├── ingestion/
│   ├── __init__.py
│   ├── pdf_parser.py         # LandingAI PDF parsing (reuse existing)
│   ├── chunker.py            # PySBD sentence splitting + table/figure handling
│   ├── embedder.py           # MedCPT Article Encoder
│   ├── typizer.py            # LLM assigns RT-ID to document (Stage 1)
│   └── normalizer.py         # Unicode/numeric normalization (NOT Jaccard)
│
├── classification/
│   ├── __init__.py
│   └── claim_classifier.py   # LLM assigns CT-ID + PICOT extraction (Stage 2 / Step 1)
│
├── retrieval/
│   ├── __init__.py
│   ├── mapping_matrix.py     # Parsed CT→RT P/A/C/N lookup table (Step 2)
│   ├── query_builder.py      # Build ES query with dynamic RT-ID boost/filter (Step 2)
│   └── reranker.py           # Cross-encoder re-ranking (Step 3)
│
├── evaluation/
│   ├── __init__.py
│   ├── substantiation_judge.py  # LLM Judge: PICOT, coverage, stats (Step 4)
│   ├── logic_gate.py            # Deterministic rule enforcement (Step 5)
│   └── audit_trail.py           # Citation metadata logging (Step 6)
│
├── prompts/
│   ├── typization_prompt.py     # System prompt for RT-ID classification
│   ├── classification_prompt.py # System prompt for CT-ID + PICOT extraction
│   └── judge_prompt.py          # System prompt for substantiation evaluation
│
└── tests/
    ├── test_typizer.py
    ├── test_classifier.py
    ├── test_mapping_matrix.py
    ├── test_query_builder.py
    ├── test_judge.py
    └── test_logic_gate.py
```

---

## Build Order

### Phase 1: Foundation (schemas + config + normalizer)
- [ ] `schemas.py` — Pydantic models
- [ ] `config.py` — Environment variables, API keys
- [ ] `ingestion/normalizer.py` — Unicode NFKC + numeric token cleaning (no Jaccard)

### Phase 2: Ingestion (Stage 1)
- [ ] `ingestion/pdf_parser.py` — Thin wrapper around existing LandingAI code
- [ ] `ingestion/chunker.py` — PySBD sentence splitting
- [ ] `ingestion/embedder.py` — MedCPT article encoder
- [ ] `prompts/typization_prompt.py` — RT-ID classification prompt
- [ ] `ingestion/typizer.py` — LLM call to assign RT-ID

### Phase 3: Classification (Stage 2 / Step 1)
- [ ] `prompts/classification_prompt.py` — CT-ID + PICOT prompt
- [ ] `classification/claim_classifier.py` — LLM call

### Phase 4: Retrieval (Steps 2-3)
- [ ] `retrieval/mapping_matrix.py` — Parse the Claim-to-Reference_Mapping.md into code
- [ ] `retrieval/query_builder.py` — Dynamic ES query with RT-ID boost/filter
- [ ] `retrieval/reranker.py` — MedCPT cross-encoder

### Phase 5: Evaluation (Steps 4-6)
- [ ] `prompts/judge_prompt.py` — Substantiation evaluation prompt
- [ ] `evaluation/substantiation_judge.py` — LLM Judge
- [ ] `evaluation/logic_gate.py` — Deterministic rules (coverage thresholds, fair balance check)
- [ ] `evaluation/audit_trail.py` — Citation metadata schema (Section 8.1)

### Phase 6: Tests
- [ ] All test files

---

## API Keys Required

| Service | Env Var | Purpose |
|---------|---------|---------|
| LandingAI | `LANDINGAI_API_KEY` | PDF parsing |
| Anthropic (Claude) | `ANTHROPIC_API_KEY` | Table/figure linearization + LLM Judge |
| Google Gemini or OpenAI | `GEMINI_API_KEY` or `OPENAI_API_KEY` | Claim classification + typization (cheaper model) |
| Elasticsearch | `ES_URL`, `ES_API_KEY` | Vector storage & search |
| HuggingFace (optional) | `HF_TOKEN` | MedCPT model download if gated |

---

## Normalization Strategy (New vs Old)

**KEEP:**
- Unicode NFKC normalization (handles "32·6%" → "32.6%")
- Whitespace collapsing
- Numeric token extraction and cleaning

**DROP:**
- Token Jaccard overlap (replaced by MedCPT semantic similarity)
- Token containment scoring (replaced by cross-encoder re-ranker)
- Fuzzy string matching (replaced by LLM Judge)

**NEW:**
- Numeric format normalization: "p<0.001" and "p < .001" must normalize to same form
- Percentage normalization: "32.6 %" and "32.6%" must match
- Ratio normalization: "4x" and "four-fold" flagged for LLM verification
