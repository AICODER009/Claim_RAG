#!/usr/bin/env python3
"""Classify claims that are missing CT-IDs in the xlsx.

Smart deduplication:
  1. Claims marked "Duplicate of row X" → inherit parent's CT-ID if available
  2. Claims with identical text → classify once, copy to all duplicates
  3. Only unique, non-inheritable texts go to LLM

Uses OpenAI GPT-5.5 (or Anthropic Claude) for classification.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from pathlib import Path

import openpyxl

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from new_pipeline.classification.claim_classifier import ClaimClassifier
from new_pipeline.config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CLAIMS_XLSX = Path(__file__).parent.parent / "claims" / "ALL_CLAIMS_COMBINED_categorized_v5.xlsx"
OUTPUT_FILE = Path(__file__).parent.parent / "claims" / "classified_missing_claims.json"

# Delay between API calls (seconds) to avoid rate limiting
API_DELAY = 0.3


def load_all_rows():
    """Load all rows from xlsx for parent-row lookups."""
    logger.info(f"Loading claims from: {CLAIMS_XLSX}")
    wb = openpyxl.load_workbook(str(CLAIMS_XLSX), read_only=True)
    ws = wb["All Claims Combined"]

    all_rows = {}
    for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        all_rows[row_num] = {
            "claim": str(row[4] or "").strip(),
            "category": str(row[10] or "").strip(),
            "ct_id": str(row[12] or "").strip(),
            "document": str(row[0] or ""),
            "page": str(row[1] or ""),
            "source_type": str(row[2] or ""),
            "ref_num": str(row[5] or ""),
            "references": str(row[6] or ""),
        }

    wb.close()
    return all_rows


def analyze_missing(all_rows):
    """Categorize missing claims into: inherit, dedup, or LLM-needed."""
    inherit = []       # Can copy CT-ID from parent row
    need_classify = []  # Need LLM classification

    for row_num, data in all_rows.items():
        claim = data["claim"]
        category = data["category"]
        ct_id = data["ct_id"]

        if not claim or len(claim) < 20 or category == "Non-claim":
            continue
        if ct_id and len(ct_id) >= 3:
            continue  # Already has CT-ID

        # Check if parent row has CT-ID
        parent_match = re.search(r"(?:Duplicate|Variation) of row (\d+)", category)
        if parent_match:
            parent_row = int(parent_match.group(1))
            parent = all_rows.get(parent_row, {})
            parent_ct = parent.get("ct_id", "")
            if parent_ct and len(parent_ct) >= 3:
                inherit.append({
                    "row": row_num,
                    "claim": claim,
                    "ct_id": parent_ct,
                    "source": f"inherited from row {parent_row}",
                    "document": data["document"],
                })
                continue

        need_classify.append({
            "row": row_num,
            "claim": claim,
            "document": data["document"],
            "category": category,
        })

    return inherit, need_classify


def deduplicate_for_classification(claims):
    """Group claims by text so we classify each unique text only once."""
    text_to_rows = {}  # claim_text -> list of row dicts
    for c in claims:
        text = c["claim"]
        if text not in text_to_rows:
            text_to_rows[text] = []
        text_to_rows[text].append(c)

    # Pick one representative per unique text
    unique = []
    for text, rows in text_to_rows.items():
        unique.append({
            "representative_row": rows[0]["row"],
            "claim": text,
            "document": rows[0]["document"],
            "all_rows": [r["row"] for r in rows],
            "count": len(rows),
        })

    return unique


def load_existing_results():
    """Load previously classified results for resume capability."""
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    return []


def save_results(results):
    """Save classification results to JSON."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(results)} results to {OUTPUT_FILE}")


def main():
    cfg = load_config()

    # Use config's provider/model
    provider = cfg.llm.classifier_provider
    if provider == "anthropic":
        api_key = cfg.llm.anthropic_api_key
        model = cfg.llm.judge_model
    else:
        api_key = cfg.llm.openai_api_key
        model = cfg.llm.classifier_model

    logger.info(f"Using {provider} / {model} for classification")

    # Load and analyze
    all_rows = load_all_rows()
    inherited, need_classify = analyze_missing(all_rows)
    unique_claims = deduplicate_for_classification(need_classify)

    logger.info(f"=== CLASSIFICATION PLAN ===")
    logger.info(f"  Inherit from parent row: {len(inherited)} (0 API calls)")
    logger.info(f"  Need classification: {len(need_classify)} claims")
    logger.info(f"  Unique texts to classify: {len(unique_claims)} (actual API calls)")
    logger.info(f"  Duplicate texts (will copy): {len(need_classify) - len(unique_claims)}")

    # Load existing results for resume
    existing = load_existing_results()
    done_rows = {r["row"] for r in existing}

    # Start with inherited results
    all_results = list(existing)

    # Add inherited CT-IDs (no API call needed)
    for item in inherited:
        if item["row"] not in done_rows:
            all_results.append({
                "row": item["row"],
                "claim": item["claim"][:200],
                "document": item["document"],
                "ct_id": item["ct_id"],
                "claim_type_name": f"Inherited from parent",
                "confidence": 1.0,
                "source": item["source"],
            })
            done_rows.add(item["row"])

    logger.info(f"Added {len(inherited)} inherited CT-IDs")

    # Initialize classifier
    classifier = ClaimClassifier(
        provider=provider,
        model=model,
        api_key=api_key,
        taxonomy_path=cfg.claim_classification_path,
    )

    # Classify unique texts
    classified_texts = {}  # claim_text -> classification result
    
    # Check which unique claims still need classification
    for existing_r in all_results:
        ct = existing_r.get("ct_id", "")
        if ct and ct != "FAILED":
            claim_text = existing_r.get("claim", "")
            if claim_text:
                classified_texts[claim_text] = existing_r

    to_classify = [u for u in unique_claims 
                   if u["claim"][:200] not in classified_texts 
                   and u["representative_row"] not in done_rows]
    
    logger.info(f"Unique texts still to classify: {len(to_classify)}")

    start_time = time.time()
    for i, item in enumerate(to_classify, 1):
        claim_text = item["claim"]
        rows = item["all_rows"]

        try:
            classification, picot = classifier.classify(claim_text)

            result_base = {
                "claim": claim_text[:200],
                "document": item["document"],
                "ct_id": classification.ct_id,
                "claim_type_name": classification.claim_type_name,
                "secondary_ct_id": classification.secondary_ct_id,
                "confidence": classification.confidence,
                "picot": {
                    "population": picot.population,
                    "intervention": picot.intervention,
                    "comparator": picot.comparator,
                    "outcome": picot.outcome,
                    "timeframe": picot.timeframe,
                },
            }

            # Add result for ALL rows with this text
            for row in rows:
                if row not in done_rows:
                    result = dict(result_base)
                    result["row"] = row
                    if len(rows) > 1:
                        result["source"] = f"classified once, copied to {len(rows)} rows"
                    all_results.append(result)
                    done_rows.add(row)

            # Progress
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            remaining = (len(to_classify) - i) / rate if rate > 0 else 0
            logger.info(
                f"  [{i}/{len(to_classify)}] {classification.ct_id} "
                f"({classification.confidence:.0%}) → {len(rows)} row(s) | "
                f"ETA: {remaining/60:.1f}min"
            )

            # Checkpoint every 25
            if i % 25 == 0:
                save_results(all_results)

        except Exception as e:
            logger.error(f"  [{i}/{len(to_classify)}] FAILED: {e}")
            for row in rows:
                if row not in done_rows:
                    all_results.append({
                        "row": row,
                        "claim": claim_text[:200],
                        "document": item["document"],
                        "ct_id": "FAILED",
                        "error": str(e),
                    })
                    done_rows.add(row)

        time.sleep(API_DELAY)

    # Final save
    save_results(all_results)

    # Summary
    elapsed = time.time() - start_time
    ct_counts = {}
    for r in all_results:
        ct = r.get("ct_id", "FAILED")
        ct_counts[ct] = ct_counts.get(ct, 0) + 1

    print(f"\n{'='*60}")
    print(f"CLASSIFICATION COMPLETE")
    print(f"{'='*60}")
    print(f"Total classified: {len(all_results)}")
    print(f"LLM calls made: {len(to_classify)}")
    print(f"Inherited from parents: {len(inherited)}")
    print(f"Time: {elapsed:.0f}s ({elapsed/60:.1f}min)")
    print(f"\nCT-ID distribution:")
    for ct, count in sorted(ct_counts.items(), key=lambda x: -x[1]):
        print(f"  {ct:15s}: {count:4d}")


if __name__ == "__main__":
    main()
