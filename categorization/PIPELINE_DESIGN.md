# VerifAI Pipeline Design & Requirements Integration

This document outlines the end-to-end architecture for integrating the new Regulatory Categorization rules (Claim-Type-Driven routing) into the VerifAI pipeline. It also addresses testing strategies, NER replacements, and specific MLR rules regarding citations.

## 1. The Updated 4-Step Architecture Flow

Based on the newly discovered constraints in the `categorization/` folder, the pipeline must be split into four distinct stages to ensure MLR compliance:

### Stage 1: Ingestion & Typization (The `indexing.py` update)
**What happens:** When a reference document (PDF) is uploaded, it must be classified before it is chunked and stored.
**Implementation:**
- Pass the first 2-3 pages to an LLM.
- Use `Reference_Document_Types.md` as the prompt context.
- The LLM assigns an `RT-ID` (e.g., `RT-101` for USPI, `RT-301` for Journal Article).
- **Storage:** Every single chunk from that document stored in Elasticsearch/Qdrant must have `{"rt_id": "RT-101"}` attached to its metadata.

### Stage 2: Pre-Retrieval Classification (The Claim entry point)
**What happens:** When a user submits a claim (e.g., *"Drug X achieved 32% abstinence"*), the system must determine the regulatory nature of the claim.
**Implementation:**
- Pass the claim to an LLM.
- Use `Claim_classification.md` as the prompt context.
- The LLM assigns a primary `CT-ID` (e.g., `CT-201` for Efficacy) and potentially a secondary `A10` tag (e.g., `CT-A01` if it's Real-World Evidence).

### Stage 3: Prioritized Retrieval (The `searching.py` update)
**What happens:** The system queries the vector database, but strictly obeys the MLR hierarchy.
**Implementation:**
- The Python code looks up the claim's `CT-ID` in the `Claim-to-Reference_Mapping.md` matrix.
- It identifies which `RT-IDs` are Primary (P), Acceptable (A), Conditional (C), or Not Acceptable (N).
- **The Query Modifier:** 
  - Apply heavy scoring boosts (e.g., +2.0) to chunks from Tier P documents.
  - Apply moderate boosts (e.g., +1.0) to Tier A documents.
  - **Hard block/Filter out** any Tier N documents (e.g., blocking preprints for efficacy claims).

### Stage 4: Post-Retrieval LLM Judge (The Evaluation phase)
**What happens:** The system evaluates if the retrieved text legally proves the claim.
**Implementation:**
The LLM evaluates the text against the `Claim_Substantiation_Requirements_v1_1.md` rules:
1. **PICOT Alignment:** Population, Intervention, Comparator, Outcome, and Timeframe must perfectly match.
2. **Coverage Score:** Are all parts of the claim proven? (Must be ≥80 to pass).
3. **Net Impression:** Does the text support the implied claim? (e.g., "4x more likely" requires finding both the 32% numerator and 8% denominator in the text).
4. **Statistical Rigor:** Are p-values or confidence intervals present to back up words like "significantly"?
5. **Fair Balance Linkage:** If it's a benefit claim, did the system also retrieve the corresponding safety warning from the PI?

---

## 2. MLR Rule: Substantiating with Footnotes/Secondary Citations

**Your Question:** *Do we need to substantiate claims with a footnote or citation from a reference? Let's say Reference A does not mention the data from its own trial, but mentions it via a citation/footnote referencing Reference B.*

**The MLR Answer:** **No, this is strictly prohibited.**
In MLR compliance, this is known as a **Secondary Citation**. If Document A says *"Drug X is highly effective [14]"*, you **cannot** use Document A to substantiate the claim. 

**The Rule:** You must always retrieve and cite the **Primary Source** (Document B). 
*Exceptions:* The only time secondary citations are acceptable is if Document A is the FDA-approved label (USPI) or an official Clinical Practice Guideline (like AHA/ACC guidelines). Otherwise, your LLM Judge must flag this and state: *"Claim is unsubstantiated; current reference relies on a secondary citation. Please provide the primary source."*

---

## 3. Why Replace NER with Embeddings (SapBERT / MedCPT)?

In the old bundle, the pipeline used `Stanza` or `d4data` for Named Entity Recognition (NER) to pull out words like "diabetes" or "headache" and do text-overlap matching. 

**Why this fails in Pharma:**
NER only extracts the *string*. If the claim says "T2DM", but the PDF says "Type 2 Diabetes Mellitus" or "adult-onset diabetes", the NER strings do not match. The old system's Jaccard overlap score would fail.

**Why Embeddings (SapBERT / UMLS Grounding) are mandatory:**
SapBERT doesn't just extract strings; it maps medical terms to a universal **UMLS Concept ID (CUI)**. 
- "T2DM" ➔ `C0011860`
- "Type 2 Diabetes Mellitus" ➔ `C0011860`
- "Non-insulin dependent diabetes" ➔ `C0011860`

By using MedCPT/SapBERT, the retrieval engine mathematically knows these are the exact same disease, drastically improving recall and preventing the LLM from missing critical clinical evidence just because the author used a synonym.

---

## 4. How to Test Each Part of the New Flow

You should build modular unit tests for each stage to ensure compliance:

### Test 1: Typization (Ingestion)
- **Input:** Pass 5 known PDFs to the ingestion agent (1 USPI, 1 Clinical Trial, 1 Poster, 1 Preprint, 1 Claims data analysis).
- **Expectation:** The vector DB metadata accurately reflects `RT-101`, `RT-201`, `RT-402`, `RT-310`, and `RT-501`.

### Test 2: Claim Classification (Pre-Retrieval)
- **Input:** Pass 10 diverse claims to the classification LLM.
- **Expectation:** It correctly assigns `CT-201` for primary efficacy, `CT-301` for safety, `CT-A01` for RWE, etc.

### Test 3: Prioritization Logic (Retrieval)
- **Test:** Write a unit test that mocks Elasticsearch. Provide a `CT-201` claim.
- **Expectation:** Ensure the query builder injects a positive weight multiplier for `RT-101` and `RT-201`, and injects a `must_not` filter for `RT-310` (Preprints).

### Test 4: The LLM Judge (Evaluation)
- **Test (PICOT Failure):** Provide a claim about "Week 24" but feed the LLM text about "Week 12". Expect it to fail the Coverage Score due to Timeframe misalignment.
- **Test (Secondary Citation):** Feed the LLM text that says *"As proven by Smith et al [12], the drug works."* Expect the LLM to reject it and demand the primary source.
- **Test (Fair Balance):** Feed the LLM a perfect efficacy match. Expect the LLM to output a flag demanding the corresponding safety linkage.
