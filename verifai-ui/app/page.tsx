import { prisma } from "@/lib/prisma";
import Link from "next/link";
import { DashboardClient } from "@/components/DashboardClient";

export const dynamic = "force-dynamic";

async function getStats() {
  try {
    const [total, results, recent, allClaims] = await Promise.all([
      prisma.claim.count(),
      prisma.substantiationResult.findMany({
        select: {
          verdict: true, coverageScore: true, runAt: true,
          claim: { select: { ctId: true, source: true, createdAt: true } },
        },
        orderBy: { runAt: "asc" },
      }),
      prisma.claim.findMany({
        take: 6,
        orderBy: { updatedAt: "desc" },
        include: {
          result: true,
          overrides: { orderBy: { overriddenAt: "desc" }, take: 1 },
        },
      }),
      prisma.claim.findMany({
        select: { source: true },
      }),
    ]);

    const pass = results.filter((r) => r.verdict === "PASS").length;
    const soft = results.filter((r) => r.verdict === "SOFT_FLAG").length;
    const block = results.filter((r) => r.verdict === "BLOCK").length;
    const pending = total - results.length;
    const normalizeScore = (s: number) => { const n = Number(s); return n > 1 ? n / 100 : n; };
    const avgScore = results.length > 0 ? results.reduce((s, r) => s + normalizeScore(r.coverageScore), 0) / results.length : 0;

    const companies = Array.from(new Set(allClaims.map((c) => c.source ?? "").filter(Boolean))).sort();

    return { total, pass, soft, block, pending, avgScore, results, recent, companies };
  } catch {
    return { total: 0, pass: 0, soft: 0, block: 0, pending: 0, avgScore: 0, results: [], recent: [], companies: [] };
  }
}

export default async function DashboardPage() {
  const { total, pass, soft, block, pending, avgScore, results, recent, companies } = await getStats();

  const serializedResults = results.map((r) => ({
    verdict: r.verdict,
    coverageScore: Number(r.coverageScore),
    runAt: r.runAt?.toISOString() ?? "",
    ctId: (r as any).claim?.ctId ?? "",
    source: (r as any).claim?.source ?? "",
  }));

  const serializedRecent = recent.map((c) => ({
    id: c.id,
    text: c.text,
    ctId: c.ctId,
    source: c.source ?? "",
    updatedAt: c.updatedAt?.toISOString() ?? "",
    verdict: c.overrides[0]?.newVerdict ?? c.result?.verdict ?? "PENDING",
  }));

  return (
    <div style={{ padding: "28px 36px" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.02em", marginBottom: 4 }}>
            Dashboard
          </h1>
          <p style={{ fontSize: 14, color: "var(--text-muted)" }}>
            Life Sciences Marketing Compliance, powered by AI
          </p>
        </div>
        <Link href="/upload" className="btn-accent" style={{ fontSize: 13, display: "flex", alignItems: "center", gap: 8, textDecoration: "none" }}>
          Substantiate Claim
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </Link>
      </div>

      <DashboardClient
        total={total}
        pass={pass}
        soft={soft}
        block={block}
        pending={pending}
        avgScore={avgScore}
        results={serializedResults}
        recent={serializedRecent}
        companies={companies}
      />
    </div>
  );
}
