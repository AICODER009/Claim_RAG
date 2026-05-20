# VerifAI MLR-Compliant Substantiation Pipeline
# New architecture implementing Claim-Type-Driven retrieval with regulatory compliance.
#
# Pipeline Stages:
#   1. Ingestion & Typization (assign RT-ID to documents)
#   2. Claim Classification (assign CT-ID to claims)
#   3. Prioritized Retrieval (filter/boost by P/A/C/N matrix)
#   4. LLM Substantiation Judge (PICOT, Coverage Score, Fair Balance)
#   5. Deterministic Logic Gate (enforce MLR rules)
#   6. Audit Trail & Output (Pass/Soft_Flag/Block)
