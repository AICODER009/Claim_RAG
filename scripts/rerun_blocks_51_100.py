#!/usr/bin/env python3
"""Minimal re-judge: only calls Claude Sonnet 4.6 on the 2 blocked claims.
NO model loading — uses pre-saved passages from the previous run via Qdrant direct lookup."""

import json, logging, os, sys, time, re
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, "D:\\pip_packages")

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env", override=True)

from qdrant_client import QdrantClient, models
from new_pipeline.config import load_config
from new_pipeline.evaluation.substantiation_judge import SubstantiationJudge
from new_pipeline.retrieval.mapping_matrix import MappingMatrix
from new_pipeline.schemas import ClaimClassification, PICOTComponents

logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BLOCKED_CLAIMS = [
    {
        "idx": 91, "row": 125, "ct_id": "CT-705",
        "doc": "VYVGART Hytrulo CIDP - FCE Presentation Deck",
        "claim": "CIDP can have a variable clinical course, with chronic progressive being the most common",
        "search_keywords": [
            ("chronic", "progressive", "common"),
            ("course", "CIDP", "progressive"),
            ("relapsing", "chronic", "common"),
        ],
    },
    {
        "idx": 99, "row": 133, "ct_id": "CT-702",
        "doc": "VYVGART Hytrulo CIDP - FCE Presentation Deck",
        "claim": "77% of 190 patients who report being dissatisfied with their symptom burden are on 1 or more treatments",
        "search_keywords": [
            ("dissatisfied", "190", "treatment"),
            ("symptom", "dissatisfied", "medications"),
            ("symptom", "satisfied", "dissatisfied"),
        ],
    },
]

OUTPUT_MD = Path(__file__).parent.parent / "claims" / "blocked_51_100_rerun.md"


def fetch_passages_by_keywords(client, collection, keyword_groups, limit=15):
    """Fetch relevant passages using keyword searches (no embedding needed)."""
    all_chunks = {}
    for kws in keyword_groups:
        must_conditions = [
            models.FieldCondition(key="text", match=models.MatchText(text=kw))
            for kw in kws
        ]
        try:
            results = client.scroll(
                collection_name=collection,
                scroll_filter=models.Filter(must=must_conditions),
                limit=20,
                with_payload=True,
            )
            for p in results[0]:
                pid = str(p.id)
                if pid not in all_chunks:
                    all_chunks[pid] = p
        except Exception as e:
            logger.warning(f"  Keyword search {kws} failed: {e}")

    # Convert to passage dicts
    passages = []
    for pid, p in all_chunks.items():
        payload = p.payload or {}
        passages.append({
            "text": payload.get("text", ""),
            "ref_id": payload.get("ref_id", ""),
            "rt_id": payload.get("rt_id", "RT-301"),
            "tier": payload.get("tier", "P"),
            "final_score": 0.03,
            "section": payload.get("section", ""),
        })

    return passages[:limit]


def main():
    cfg = load_config()
    qdrant = QdrantClient(url=cfg.qdrant.url, api_key=cfg.qdrant.api_key, timeout=30)
    matrix = MappingMatrix(cfg.claim_mapping_path)

    judge = SubstantiationJudge(
        api_key=cfg.llm.anthropic_api_key,
        model="claude-sonnet-4-6",
        requirements_path=cfg.substantiation_requirements_path,
    )

    md = ["# Blocked Claims 51-100 Re-run — Updated Judge (Arithmetic Exception)\n"]
    md.append(f"**Date:** {time.strftime('%Y-%m-%d %H:%M')}")
    md.append("**Change:** Added simple arithmetic exception to rule 6 in judge prompt\n")

    for claim_data in BLOCKED_CLAIMS:
        claim_text = claim_data["claim"]
        ct_id = claim_data["ct_id"]
        idx = claim_data["idx"]
        t0 = time.time()

        logger.info(f"\n{'='*60}")
        logger.info(f"  Claim #{idx}: {claim_text[:80]}...")
        logger.info(f"{'='*60}")

        try:
            # Fetch passages via keyword search (no models needed)
            passages = fetch_passages_by_keywords(
                qdrant, cfg.qdrant.collection_name,
                claim_data["search_keywords"],
                limit=15
            )
            logger.info(f"  Retrieved {len(passages)} passages via keyword search")
            for j, p in enumerate(passages[:15]):
                ref = p.get("ref_id", "")
                text_preview = p.get("text", "")[:100].replace("\n", " ")
                logger.info(f"    [{j+1}] {ref[:40]} | {text_preview}")

            # Judge
            classification = ClaimClassification(ct_id=ct_id, claim_type_name=ct_id, confidence=0.9)
            picot = PICOTComponents()

            if passages:
                raw = judge.evaluate(
                    claim_text=claim_text,
                    classification=classification,
                    picot=picot,
                    evidence_passages=passages[:15],
                )
            else:
                raw = {"coverage_score": 0, "overall_assessment": "No passages.", "sub_assertions": []}

            coverage = raw.get("coverage_score", 0)
            if isinstance(coverage, str):
                try: coverage = float(coverage.replace("%", ""))
                except: coverage = 0

            if coverage >= 80: verdict = "PASS"
            elif coverage >= 60: verdict = "SOFT_FLAG"
            else: verdict = "BLOCK"

            elapsed = time.time() - t0
            emoji = {"PASS": "✅", "SOFT_FLAG": "⚠️", "BLOCK": "❌"}.get(verdict, "❓")
            logger.info(f"  → {emoji} {verdict} ({coverage}%) in {elapsed:.1f}s")

            md.append(f"\n## #{idx} (Row {claim_data['row']}) — {emoji} {verdict} ({coverage}%)\n")
            md.append(f"- **CT-ID:** `{ct_id}` | **Time:** {elapsed:.1f}s")
            md.append(f"- **Document:** {claim_data['doc']}")
            md.append(f"- **Claim:** {claim_text}\n")

            # Passage table
            md.append("<details><summary>📋 All passages sent to judge</summary>\n")
            md.append("| # | RT-ID | Tier | ref_id | Preview |")
            md.append("|---|-------|------|--------|---------|")
            for j, p in enumerate(passages[:15]):
                preview = p.get("text", "")[:80].replace("\n", " ").replace("|", "/")
                md.append(
                    f"| {j+1} | `{p.get('rt_id','?')}` | {p.get('tier','?')} "
                    f"| {p.get('ref_id','?')[:40]} | {preview} |"
                )
            md.append("\n</details>\n")

            subs = raw.get("sub_assertions", [])
            if subs:
                md.append("**Sub-assertions:**\n")
                for sa in subs:
                    covered = sa.get("is_covered", False)
                    icon = "✅" if covered else "❌"
                    text = sa.get("sub_assertion", "?")
                    evidence = sa.get("evidence_text", "")
                    md.append(f"- {icon} {text}")
                    if evidence and covered:
                        md.append(f'  > *"{evidence[:200]}"*')
                md.append("")

            if raw.get("overall_assessment"):
                md.append(f"**Assessment:** {raw['overall_assessment'][:800]}\n")

            md.append("---\n")

        except Exception as e:
            logger.error(f"  ERROR: {e}", exc_info=True)
            md.append(f"\n## #{idx} — ❓ ERROR\n- {str(e)}\n---\n")

    OUTPUT_MD.write_text("\n".join(md), encoding="utf-8")
    logger.info(f"\nReport: {OUTPUT_MD}")
    print(f"\nDONE — report at {OUTPUT_MD}")


if __name__ == "__main__":
    main()
