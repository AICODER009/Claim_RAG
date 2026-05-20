import { prisma } from "@/lib/prisma";
import { ReportClient } from "@/components/ReportClient";

export const dynamic = "force-dynamic";

async function getReportData() {
  try {
    const [claims, results, deleted] = await Promise.all([
      prisma.claim.findMany({
        include: {
          result: true,
          overrides: { orderBy: { overriddenAt: "desc" }, take: 1 },
        },
        orderBy: { createdAt: "desc" },
      }),
      prisma.substantiationResult.findMany({
        select: { verdict: true, coverageScore: true },
      }),
      // Best-effort — table may not exist yet if migration hasn't run
      (prisma as any).deletedClaim.findMany({
        orderBy: { deletedAt: "desc" },
      }).catch(() => []),
    ]);

    const total = claims.length;
    const pass = results.filter((r: any) => r.verdict === "PASS").length;
    const soft = results.filter((r: any) => r.verdict === "SOFT_FLAG").length;
    const block = results.filter((r: any) => r.verdict === "BLOCK").length;
    const pending = total - results.length;
    const norm = (v: unknown) => { const n = Number(v ?? 0); return n > 1 ? n / 100 : n; };
    const avgScore = results.length > 0
      ? results.reduce((s: number, r: any) => s + norm(r.coverageScore), 0) / results.length
      : 0;

    const claimsData = claims.map((c: any) => ({
      id: c.id,
      text: c.text,
      ctId: c.ctId,
      source: c.source ?? "",
      verdict: c.overrides[0]?.newVerdict ?? c.result?.verdict ?? "PENDING",
      score: norm(c.result?.coverageScore ?? 0),
      reasoning: c.result?.assessment ?? "",
      createdAt: c.createdAt.toISOString(),
    }));

    const deletedData = deleted.map((d: any) => ({
      id: d.id,
      originalId: d.originalId,
      text: d.text,
      ctId: d.ctId,
      source: d.source ?? "",
      verdict: d.verdict,
      score: norm(d.score),
      deletedAt: d.deletedAt.toISOString(),
    }));

    const companies = Array.from(new Set([
      ...claimsData.map((c: any) => c.source),
      ...deletedData.map((d: any) => d.source),
    ].filter(Boolean))).sort() as string[];

    return { total, pass, soft, block, pending, avgScore: norm(avgScore), claims: claimsData, deleted: deletedData, companies };
  } catch {
    return { total: 0, pass: 0, soft: 0, block: 0, pending: 0, avgScore: 0, claims: [], deleted: [], companies: [] };
  }
}

export default async function ReportPage() {
  const data = await getReportData();
  return <ReportClient data={data} />;
}
