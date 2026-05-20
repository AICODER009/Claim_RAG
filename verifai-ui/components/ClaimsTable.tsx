"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

const VERDICT_STYLES: Record<string, { bg: string; color: string; dot: string }> = {
  PASS: { bg: "rgba(16,185,129,0.1)", color: "#34d399", dot: "#10b981" },
  SOFT_FLAG: { bg: "rgba(245,158,11,0.1)", color: "#fbbf24", dot: "#f59e0b" },
  BLOCK: { bg: "rgba(239,68,68,0.1)", color: "#f87171", dot: "#ef4444" },
  PENDING: { bg: "rgba(100,116,139,0.1)", color: "#94a3b8", dot: "#64748b" },
};

type ClaimRow = {
  id: string;
  text: string;
  ctId: string;
  source?: string;
  updatedAt?: string;
  result: { verdict: string; coverageScore: number } | null;
  overrides: { newVerdict: string }[];
};

const inputStyle: React.CSSProperties = {
  height: 32, padding: "0 10px", borderRadius: 8, fontSize: 12,
  border: "1px solid var(--border-subtle)", background: "var(--bg-tertiary)",
  color: "var(--text-primary)", outline: "none", cursor: "pointer",
};

export function ClaimsTable({ claims }: { claims: ClaimRow[] }) {
  const router = useRouter();
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [deleting, setDeleting] = useState(false);
  const [confirmAll, setConfirmAll] = useState(false);

  // ── Filters ────────────────────────────────────────────────────────────────
  const [companyFilter, setCompanyFilter] = useState("all");
  const [verdictFilter, setVerdictFilter] = useState("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  // Derive unique companies from claims
  const companies = useMemo(() => {
    const s = new Set(claims.map((c) => c.source || "").filter(Boolean));
    return Array.from(s).sort();
  }, [claims]);

  // Apply filters
  const filtered = useMemo(() => {
    return claims.filter((c) => {
      if (companyFilter !== "all" && (c.source || "") !== companyFilter) return false;
      const verdict = c.overrides[0]?.newVerdict ?? c.result?.verdict ?? "PENDING";
      if (verdictFilter !== "all" && verdict !== verdictFilter) return false;
      if (dateFrom && c.updatedAt && c.updatedAt < dateFrom) return false;
      if (dateTo && c.updatedAt && c.updatedAt > dateTo + "T23:59:59") return false;
      return true;
    });
  }, [claims, companyFilter, verdictFilter, dateFrom, dateTo]);

  const hasFilters = companyFilter !== "all" || verdictFilter !== "all" || dateFrom || dateTo;

  const allSelected = filtered.length > 0 && selected.size === filtered.length;

  function toggleOne(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }

  function toggleAll() {
    if (allSelected) {
      setSelected(new Set());
    } else {
      setSelected(new Set(filtered.map((c) => c.id)));
    }
  }

  async function deleteSelected() {
    if (selected.size === 0) return;
    setDeleting(true);
    const ids = Array.from(selected);
    await Promise.all(
      ids.map((id) =>
        fetch("/api/claims", {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id }),
        })
      )
    );
    setSelected(new Set());
    setDeleting(false);
    setConfirmAll(false);
    router.refresh();
  }

  async function deleteOne(id: string) {
    await fetch("/api/claims", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
    setSelected((prev) => { const n = new Set(prev); n.delete(id); return n; });
    router.refresh();
  }

  const checkboxStyle: React.CSSProperties = {
    width: 16, height: 16, borderRadius: 4,
    border: "1.5px solid var(--border-subtle)",
    background: "var(--bg-tertiary)",
    cursor: "pointer", display: "flex",
    alignItems: "center", justifyContent: "center",
    flexShrink: 0, transition: "all 0.15s",
  };

  return (
    <>
      {/* ── Filter Bar ───────────────────────────────────────────────────── */}
      <div style={{
        display: "flex", alignItems: "center", gap: 10, marginBottom: 12,
        flexWrap: "wrap",
      }}>
        {/* Company / Source */}
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
          </svg>
          <select value={companyFilter} onChange={(e) => setCompanyFilter(e.target.value)} style={inputStyle}>
            <option value="all">All Companies</option>
            {companies.map((c) => <option key={c} value={c}>{c}</option>)}
            {companies.length === 0 && <option value="none" disabled>No companies tagged</option>}
          </select>
        </div>

        {/* Verdict */}
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
          </svg>
          <select value={verdictFilter} onChange={(e) => setVerdictFilter(e.target.value)} style={inputStyle}>
            <option value="all">All Verdicts</option>
            <option value="PASS">Pass</option>
            <option value="SOFT_FLAG">Soft Flag</option>
            <option value="BLOCK">Block</option>
            <option value="PENDING">Pending</option>
          </select>
        </div>

        {/* Date From */}
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)}
            style={{ ...inputStyle, width: 130 }} title="From date" />
          <span style={{ fontSize: 11, color: "var(--text-muted)" }}>→</span>
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)}
            style={{ ...inputStyle, width: 130 }} title="To date" />
        </div>

        {/* Clear filters */}
        {hasFilters && (
          <button
            onClick={() => { setCompanyFilter("all"); setVerdictFilter("all"); setDateFrom(""); setDateTo(""); }}
            style={{
              height: 32, padding: "0 12px", borderRadius: 8, fontSize: 11, fontWeight: 600,
              border: "1px solid var(--border-subtle)", background: "transparent",
              color: "var(--text-muted)", cursor: "pointer", display: "flex", alignItems: "center", gap: 5,
            }}
          >
            ✕ Clear
          </button>
        )}

        <span style={{ marginLeft: "auto", fontSize: 11, color: "var(--text-muted)" }}>
          {filtered.length} of {claims.length} claim{claims.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Toolbar — shows when items are selected */}
      {selected.size > 0 && (
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "10px 16px", marginBottom: 10, borderRadius: 10,
          background: "rgba(239,68,68,0.06)", border: "1px solid rgba(239,68,68,0.15)",
        }}>
          <span style={{ fontSize: 12, color: "var(--text-secondary)", fontWeight: 500 }}>
            {selected.size} claim{selected.size > 1 ? "s" : ""} selected
          </span>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={() => { setSelected(new Set()); setConfirmAll(false); }}
              style={{
                padding: "5px 14px", borderRadius: 6, fontSize: 11, fontWeight: 600,
                border: "1px solid var(--border-subtle)", background: "transparent",
                color: "var(--text-muted)", cursor: "pointer",
              }}
            >
              Clear
            </button>
            {!confirmAll ? (
              <button
                onClick={() => setConfirmAll(true)}
                style={{
                  padding: "5px 14px", borderRadius: 6, fontSize: 11, fontWeight: 600,
                  border: "1px solid #fecaca", background: "#fef2f2",
                  color: "#dc2626", cursor: "pointer",
                  display: "flex", alignItems: "center", gap: 5,
                }}
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="3 6 5 6 21 6" />
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                </svg>
                Delete Selected
              </button>
            ) : (
              <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                <span style={{ fontSize: 11, color: "#dc2626", fontWeight: 600 }}>Confirm?</span>
                <button
                  onClick={deleteSelected}
                  disabled={deleting}
                  style={{
                    padding: "5px 14px", borderRadius: 6, fontSize: 11, fontWeight: 700,
                    border: "none", background: "#dc2626", color: "#fff",
                    cursor: "pointer", opacity: deleting ? 0.5 : 1,
                  }}
                >
                  {deleting ? "Deleting…" : `Yes, delete ${selected.size}`}
                </button>
                <button
                  onClick={() => setConfirmAll(false)}
                  style={{
                    padding: "5px 14px", borderRadius: 6, fontSize: 11,
                    border: "1px solid var(--border-subtle)", background: "transparent",
                    color: "var(--text-muted)", cursor: "pointer",
                  }}
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Table */}
      <div className="glass-card-static" style={{ overflow: "hidden" }}>
        {/* Header */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "36px 1fr 90px 110px 90px 40px",
          gap: 10, padding: "12px 16px",
          borderBottom: "1px solid var(--border-subtle)",
          background: "var(--bg-tertiary)",
          alignItems: "center",
        }}>
          <div
            onClick={toggleAll}
            style={{
              ...checkboxStyle,
              background: allSelected ? "var(--accent-coral)" : "var(--bg-tertiary)",
              borderColor: allSelected ? "var(--accent-coral)" : "var(--border-subtle)",
            }}
          >
            {allSelected && (
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            )}
          </div>
          {["Claim", "CT-ID", "Score", "Verdict", ""].map((h) => (
            <p key={h} style={{
              fontSize: 10, fontWeight: 700, color: "var(--text-muted)",
              textTransform: "uppercase", letterSpacing: "0.1em",
            }}>
              {h}
            </p>
          ))}
        </div>

        {/* Rows */}
        {filtered.length === 0 ? (
          <div style={{ padding: "40px 20px", textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>
            No claims match the current filters.
          </div>
        ) : filtered.map((claim, i) => {
          const activeVerdict = claim.overrides[0]?.newVerdict ?? claim.result?.verdict ?? "PENDING";
          const rawScore = Number(claim.result?.coverageScore ?? 0);
          const score = rawScore > 1 ? rawScore / 100 : rawScore;
          const vs = VERDICT_STYLES[activeVerdict] ?? VERDICT_STYLES.PENDING;
          const isSelected = selected.has(claim.id);

          return (
            <div
              key={claim.id}
              className={`claim-row stagger-${Math.min(i + 1, 4)}`}
              style={{
                display: "grid",
                gridTemplateColumns: "36px 1fr 90px 110px 90px 40px",
                gap: 10, padding: "12px 16px",
                borderBottom: "1px solid var(--border-subtle)",
                alignItems: "center",
                background: isSelected ? "rgba(255,95,109,0.04)" : "transparent",
                transition: "background 0.15s",
              }}
            >
              {/* Checkbox */}
              <div
                onClick={(e) => { e.stopPropagation(); toggleOne(claim.id); }}
                style={{
                  ...checkboxStyle,
                  background: isSelected ? "var(--accent-coral)" : "var(--bg-tertiary)",
                  borderColor: isSelected ? "var(--accent-coral)" : "var(--border-subtle)",
                }}
              >
                {isSelected && (
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                )}
              </div>

              {/* Claim text + company tag */}
              <div style={{ overflow: "hidden" }}>
                <Link href={`/claims/${claim.id}`} style={{
                  fontSize: 13, color: "var(--text-primary)",
                  overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                  textDecoration: "none", display: "block",
                }}>
                  {claim.text}
                </Link>
                {claim.source && (
                  <span style={{
                    fontSize: 9, fontWeight: 600, color: "#818cf8",
                    background: "rgba(129,140,248,0.08)", borderRadius: 4,
                    padding: "1px 5px", display: "inline-block", marginTop: 2,
                  }}>{claim.source}</span>
                )}
              </div>

              {/* CT-ID */}
              <span style={{
                fontSize: 11, fontWeight: 600, color: "#818cf8",
                fontFamily: "var(--font-mono)",
              }}>
                {claim.ctId}
              </span>

              {/* Score bar */}
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <div style={{
                  flex: 1, height: 4, background: "var(--border-subtle)",
                  borderRadius: 99, overflow: "hidden",
                }}>
                  <div style={{
                    height: "100%", width: `${Math.round(score * 100)}%`,
                    borderRadius: 99,
                    background: score >= 0.8
                      ? "linear-gradient(90deg, #10b981, #34d399)"
                      : score >= 0.6
                      ? "linear-gradient(90deg, #f59e0b, #fbbf24)"
                      : "linear-gradient(90deg, #ef4444, #f87171)",
                    transition: "width 1s ease",
                  }} />
                </div>
                <span style={{
                  fontSize: 11, fontFamily: "var(--font-mono)",
                  color: "var(--text-muted)", width: 32, textAlign: "right",
                }}>
                  {Math.round(score * 100)}%
                </span>
              </div>

              {/* Verdict badge */}
              <span style={{
                display: "inline-flex", alignItems: "center", gap: 5,
                padding: "3px 10px", borderRadius: 99,
                fontSize: 10, fontWeight: 600, letterSpacing: "0.04em",
                background: vs.bg, color: vs.color, justifySelf: "start",
              }}>
                <span style={{
                  width: 5, height: 5, borderRadius: "50%", background: vs.dot,
                }} />
                {activeVerdict.replace("_", " ")}
              </span>

              {/* Delete button */}
              <button
                onClick={(e) => { e.stopPropagation(); deleteOne(claim.id); }}
                title="Delete claim"
                style={{
                  width: 26, height: 26, borderRadius: 6,
                  border: "1px solid transparent", background: "transparent",
                  color: "var(--text-muted)", cursor: "pointer",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  transition: "all 0.15s", opacity: 0.4,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.opacity = "1";
                  e.currentTarget.style.color = "#ef4444";
                  e.currentTarget.style.borderColor = "rgba(239,68,68,0.2)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.opacity = "0.4";
                  e.currentTarget.style.color = "var(--text-muted)";
                  e.currentTarget.style.borderColor = "transparent";
                }}
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="3 6 5 6 21 6" />
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                </svg>
              </button>
            </div>
          );
        })}
      </div>
    </>
  );
}
