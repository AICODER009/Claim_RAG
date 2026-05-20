import { prisma } from "@/lib/prisma";
import Link from "next/link";
import { ClaimsTable } from "@/components/ClaimsTable";

export const dynamic = "force-dynamic";

async function getClaims() {
  try {
    return await prisma.claim.findMany({
      orderBy: { updatedAt: "desc" },
      include: {
        result: { select: { verdict: true, coverageScore: true } },
        overrides: { orderBy: { overriddenAt: "desc" }, take: 1 },
      },
    });
  } catch {
    return [];
  }
}

export default async function ClaimsPage() {
  const claims = await getClaims();

  // Serialize for client component
  const serialized = claims.map((c) => ({
    id: c.id,
    text: c.text,
    ctId: c.ctId,
    source: c.source ?? "",
    updatedAt: c.updatedAt?.toISOString() ?? "",
    result: c.result ? { verdict: c.result.verdict, coverageScore: c.result.coverageScore } : null,
    overrides: c.overrides.map((o) => ({ newVerdict: o.newVerdict })),
  }));

  return (
    <div style={{ padding: "28px 36px" }}>
      {/* Header */}
      <div style={{
        display: "flex", alignItems: "flex-start",
        justifyContent: "space-between", marginBottom: 24,
      }}>
        <div>
          <h1 style={{
            fontSize: 24, fontWeight: 700,
            letterSpacing: "-0.02em", marginBottom: 4,
            color: "var(--text-primary)",
          }}>
            Claims
          </h1>
          <p style={{ fontSize: 14, color: "var(--text-muted)" }}>
            {claims.length} claim{claims.length !== 1 ? "s" : ""} in the substantiation registry
          </p>
        </div>
        <Link
          href="/upload"
          className="btn-accent"
          style={{
            fontSize: 13, display: "flex", alignItems: "center",
            gap: 8, textDecoration: "none",
          }}
        >
          + New Claim
        </Link>
      </div>

      {/* Claims Table */}
      {claims.length > 0 ? (
        <ClaimsTable claims={serialized} />
      ) : (
        <div className="glass-card-static" style={{ padding: "60px 40px", textAlign: "center" }}>
          <div style={{
            width: 60, height: 60, margin: "0 auto 20px",
            borderRadius: "50%", background: "rgba(255,107,107,0.08)",
            border: "1px solid rgba(255,107,107,0.15)",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ff8e53" strokeWidth="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
          </div>
          <p style={{ fontSize: 15, color: "var(--text-muted)", marginBottom: 8 }}>
            No claims in the registry yet
          </p>
          <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 20 }}>
            Substantiate your first pharmaceutical claim to get started
          </p>
          <Link href="/upload" className="btn-accent" style={{
            display: "inline-flex", fontSize: 13, textDecoration: "none",
          }}>
            Substantiate a Claim →
          </Link>
        </div>
      )}
    </div>
  );
}
