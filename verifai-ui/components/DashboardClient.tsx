"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { DashboardCharts } from "@/components/DashboardCharts";
import { FloatingClaims } from "@/components/FloatingClaims";

type ResultRow = {
  verdict: string;
  coverageScore: number;
  runAt: string;
  ctId: string;
  source: string;
};

type RecentRow = {
  id: string;
  text: string;
  ctId: string;
  source: string;
  updatedAt: string;
  verdict: string;
};

const VERDICT_STYLES: Record<string, { bg: string; color: string; dot: string }> = {
  PASS: { bg: "#ecfdf5", color: "#059669", dot: "#10b981" },
  SOFT_FLAG: { bg: "#fffbeb", color: "#d97706", dot: "#f59e0b" },
  BLOCK: { bg: "#fef2f2", color: "#dc2626", dot: "#ef4444" },
  PENDING: { bg: "#f8fafc", color: "#64748b", dot: "#94a3b8" },
};

const inputStyle: React.CSSProperties = {
  height: 32, padding: "0 10px", borderRadius: 8, fontSize: 12,
  border: "1px solid var(--border-subtle)", background: "var(--bg-tertiary)",
  color: "var(--text-primary)", outline: "none", cursor: "pointer",
};

export function DashboardClient({
  total, pass, soft, block, pending, avgScore,
  results, recent, companies,
}: {
  total: number; pass: number; soft: number; block: number; pending: number; avgScore: number;
  results: ResultRow[]; recent: RecentRow[]; companies: string[];
}) {
  const [companyFilter, setCompanyFilter] = useState("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const hasFilters = companyFilter !== "all" || dateFrom || dateTo;

  const filteredResults = useMemo(() => {
    return results.filter((r) => {
      if (companyFilter !== "all" && r.source !== companyFilter) return false;
      if (dateFrom && r.runAt < dateFrom) return false;
      if (dateTo && r.runAt > dateTo + "T23:59:59") return false;
      return true;
    });
  }, [results, companyFilter, dateFrom, dateTo]);

  const filteredRecent = useMemo(() => {
    return recent.filter((r) => {
      if (companyFilter !== "all" && r.source !== companyFilter) return false;
      if (dateFrom && r.updatedAt < dateFrom) return false;
      if (dateTo && r.updatedAt > dateTo + "T23:59:59") return false;
      return true;
    });
  }, [recent, companyFilter, dateFrom, dateTo]);

  // Recompute KPIs from filtered results
  const fPass = filteredResults.filter((r) => r.verdict === "PASS").length;
  const fSoft = filteredResults.filter((r) => r.verdict === "SOFT_FLAG").length;
  const fBlock = filteredResults.filter((r) => r.verdict === "BLOCK").length;
  const fPending = (hasFilters ? filteredResults.length : total) - filteredResults.length;
  const normalizeScore = (s: number) => { const n = Number(s); return n > 1 ? n / 100 : n; };
  const fAvgScore = filteredResults.length > 0
    ? filteredResults.reduce((s, r) => s + normalizeScore(r.coverageScore), 0) / filteredResults.length
    : 0;
  const fTotal = hasFilters ? filteredResults.length : total;

  const kpis = [
    { label: "Total Claims", value: hasFilters ? fTotal : total, color: "#6366f1",
      icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6366f1" strokeWidth="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg> },
    { label: "Substantiated", value: fPass, color: "#10b981",
      icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="1.5"><circle cx="12" cy="12" r="10"/><path d="M9 12l2 2 4-4"/></svg> },
    { label: "Flagged", value: fSoft, color: "#f59e0b",
      icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="1.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg> },
    { label: "Blocked", value: fBlock, color: "#ef4444",
      icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="1.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg> },
  ];

  return (
    <>
      {/* ── Filter Bar ───────────────────────────────────────────────────── */}
      <div style={{
        display: "flex", alignItems: "center", gap: 10, marginBottom: 20,
        padding: "10px 14px", borderRadius: 10,
        background: "var(--bg-tertiary)", border: "1px solid var(--border-subtle)",
        flexWrap: "wrap",
      }}>
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2">
          <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
        </svg>
        <span style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Filters</span>

        {/* Company */}
        <select value={companyFilter} onChange={(e) => setCompanyFilter(e.target.value)} style={inputStyle}>
          <option value="all">All Companies</option>
          {companies.map((c) => <option key={c} value={c}>{c}</option>)}
          {companies.length === 0 && <option value="none" disabled>No companies tagged</option>}
        </select>

        {/* Date range */}
        <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)}
          style={{ ...inputStyle, width: 130 }} title="From date" />
        <span style={{ fontSize: 11, color: "var(--text-muted)" }}>→</span>
        <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)}
          style={{ ...inputStyle, width: 130 }} title="To date" />

        {hasFilters && (
          <button
            onClick={() => { setCompanyFilter("all"); setDateFrom(""); setDateTo(""); }}
            style={{
              height: 32, padding: "0 12px", borderRadius: 8, fontSize: 11, fontWeight: 600,
              border: "1px solid var(--border-subtle)", background: "transparent",
              color: "var(--text-muted)", cursor: "pointer",
            }}
          >
            ✕ Clear
          </button>
        )}

        {hasFilters && (
          <span style={{ marginLeft: "auto", fontSize: 11, color: "var(--text-muted)" }}>
            Showing {filteredResults.length} of {results.length} results
          </span>
        )}
      </div>

      {/* KPI Row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 24 }}>
        {kpis.map(({ label, value, color, icon }, i) => (
          <div key={label} className={`glass-card stagger-${i + 1}`} style={{ padding: "18px 20px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
              <p style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</p>
              {icon}
            </div>
            <p style={{ fontSize: 32, fontWeight: 800, letterSpacing: "-0.03em", color: value > 0 ? color : "var(--text-muted)" }}>{value}</p>
          </div>
        ))}
      </div>

      {/* Avg Coverage */}
      <div className="glass-card-static" style={{ padding: "16px 20px", marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
          <div>
            <p style={{ fontSize: 13, color: "var(--text-secondary)" }}>
              Average Coverage Score
              <span style={{ color: "var(--text-primary)", fontWeight: 600, margin: "0 4px" }}>·</span>
              <span style={{ color: "var(--text-primary)", fontWeight: 600 }}>{filteredResults.length}</span>
              <span style={{ color: "var(--text-muted)", fontSize: 12 }}> substantiated claim{filteredResults.length !== 1 ? "s" : ""}</span>
              {hasFilters && <span style={{ fontSize: 11, color: "var(--text-muted)", marginLeft: 8 }}>(filtered)</span>}
            </p>
            <p style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 3 }}>
              How it's calculated: sum of each claim's evidence coverage score (0–100%) ÷ number of claims judged
            </p>
          </div>
          <div style={{ textAlign: "right" }}>
            <span className="gradient-text" style={{ fontSize: 22, fontWeight: 800 }}>{Math.round(fAvgScore * 100)}%</span>
            <p style={{ fontSize: 9, color: fAvgScore >= 0.8 ? "#10b981" : fAvgScore >= 0.6 ? "#f59e0b" : "#ef4444", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", marginTop: 2 }}>
              {fAvgScore >= 0.8 ? "✓ Strong" : fAvgScore >= 0.6 ? "⚠ Moderate" : "✗ Weak"}
            </p>
          </div>
        </div>
        <div className="score-bar-track">
          <div className={`score-bar-fill ${fAvgScore >= 0.8 ? "pass" : fAvgScore >= 0.6 ? "soft" : "block"}`} style={{ width: `${Math.round(fAvgScore * 100)}%` }} />
        </div>
        {/* Threshold markers */}
        <div style={{ position: "relative", height: 14, marginTop: 4 }}>
          <span style={{ position: "absolute", left: "60%", fontSize: 8, color: "var(--text-muted)", transform: "translateX(-50%)" }}>60% MLR min</span>
          <span style={{ position: "absolute", left: "80%", fontSize: 8, color: "var(--text-muted)", transform: "translateX(-50%)" }}>80% target</span>
        </div>
      </div>

      {/* Charts */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 24 }}>
        <DashboardCharts
          verdictCounts={{ PASS: fPass, SOFT_FLAG: fSoft, BLOCK: fBlock, PENDING: fPending }}
          scores={filteredResults.map((r) => { const n = Number(r.coverageScore); return Math.round(n > 1 ? n : n * 100); })}
          claimLabels={filteredResults.map((r) => r.ctId)}
        />
      </div>

      {/* Bottom row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <FloatingClaims />

        <div className="glass-card-static" style={{ padding: 20 }}>
          <h2 style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 14 }}>
            Recent Activity {hasFilters && <span style={{ fontWeight: 400, textTransform: "none", letterSpacing: 0 }}>(filtered)</span>}
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {filteredRecent.length > 0 ? filteredRecent.slice(0, 6).map((claim) => {
              const s = VERDICT_STYLES[claim.verdict] ?? VERDICT_STYLES.PENDING;
              return (
                <Link key={claim.id} href={`/claims/${claim.id}`} style={{
                  display: "flex", alignItems: "center", gap: 10, padding: "8px 10px", borderRadius: 8,
                  textDecoration: "none", transition: "background 0.2s",
                }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ fontSize: 12, color: "var(--text-secondary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {claim.text.slice(0, 60)}…
                    </p>
                    <div style={{ display: "flex", gap: 6, alignItems: "center", marginTop: 2 }}>
                      <p style={{ fontSize: 10, color: "var(--text-muted)" }}>{claim.ctId}</p>
                      {claim.source && <span style={{ fontSize: 9, color: "#818cf8", background: "rgba(129,140,248,0.08)", borderRadius: 4, padding: "1px 5px" }}>{claim.source}</span>}
                    </div>
                  </div>
                  <span style={{
                    display: "inline-flex", alignItems: "center", gap: 5, padding: "3px 9px",
                    borderRadius: 99, fontSize: 10, fontWeight: 600, background: s.bg, color: s.color,
                  }}>
                    <span style={{ width: 5, height: 5, borderRadius: "50%", background: s.dot }} />
                    {claim.verdict.replace("_", " ")}
                  </span>
                </Link>
              );
            }) : (
              <div style={{ padding: "36px 0", textAlign: "center" }}>
                <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 10 }}>
                  {hasFilters ? "No claims match the current filters" : "No claims yet"}
                </p>
                {!hasFilters && (
                  <Link href="/upload" className="btn-accent" style={{ fontSize: 12, padding: "7px 18px", display: "inline-flex", textDecoration: "none" }}>
                    Run your first claim →
                  </Link>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
