import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function POST(req: NextRequest) {
  const { claimId, claimText, ctId } = await req.json();
  if (!claimId || !claimText || !ctId) {
    return NextResponse.json({ error: "Missing fields" }, { status: 400 });
  }

  const sidecarUrl = process.env.SIDECAR_URL ?? "http://127.0.0.1:8001";

  // Call the FastAPI sidecar
  let sidecarData;
  try {
    const res = await fetch(`${sidecarUrl}/run_claim`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ claim_text: claimText, ct_id: ctId, top_k: 20 }),
      // Allow up to 3 minutes for judge + retrieval
      signal: AbortSignal.timeout(180_000),
    });
    if (!res.ok) {
      const err = await res.text();
      return NextResponse.json({ error: `Sidecar error: ${err}` }, { status: 502 });
    }
    sidecarData = await res.json();
  } catch (e) {
    return NextResponse.json({ error: `Sidecar unreachable: ${e}` }, { status: 503 });
  }

  const safeStr = (v: unknown) => (v == null ? "" : typeof v === "object" ? JSON.stringify(v) : String(v));
  const safeNum = (v: unknown) => { const n = Number(v); return isNaN(n) ? 0 : n > 1 ? n / 100 : n; };

  await prisma.substantiationResult.upsert({
    where: { claimId },
    create: {
      claimId,
      coverageScore: safeNum(sidecarData.coverage_score),
      verdict: safeStr(sidecarData.verdict) || "BLOCK",
      assessment: safeStr(sidecarData.assessment),
      subAssertions: JSON.stringify(sidecarData.sub_assertions ?? []),
      passages: JSON.stringify(sidecarData.passages ?? []),
      picotAlignment: JSON.stringify(sidecarData.picot_alignment ?? {}),
      rewrittenQuery: safeStr(sidecarData.rewritten_query),
      modelJudge: safeStr(sidecarData.model_judge),
      modelRewriter: safeStr(sidecarData.model_rewriter),
    },
    update: {
      coverageScore: safeNum(sidecarData.coverage_score),
      verdict: safeStr(sidecarData.verdict) || "BLOCK",
      assessment: safeStr(sidecarData.assessment),
      subAssertions: JSON.stringify(sidecarData.sub_assertions ?? []),
      passages: JSON.stringify(sidecarData.passages ?? []),
      picotAlignment: JSON.stringify(sidecarData.picot_alignment ?? {}),
      rewrittenQuery: safeStr(sidecarData.rewritten_query),
      modelJudge: safeStr(sidecarData.model_judge),
      modelRewriter: safeStr(sidecarData.model_rewriter),
      runAt: new Date(),
    },
  });

  // Touch claim updatedAt
  await prisma.claim.update({ where: { id: claimId }, data: { updatedAt: new Date() } });

  return NextResponse.json({
    ok: true,
    verdict: sidecarData.verdict,
    coverageScore: sidecarData.coverage_score,
    reasoning: sidecarData.assessment,
  });
}
