"use client";

import { useRef, useState, useMemo } from "react";

type ClaimRow = {
  id: string;
  text: string;
  ctId: string;
  source: string;
  verdict: string;
  score: number;
  reasoning: string;
  createdAt: string;
};

type DeletedRow = {
  id: string;
  originalId: string;
  text: string;
  ctId: string;
  source: string;
  verdict: string;
  score: number;
  deletedAt: string;
};

type ReportData = {
  total: number;
  pass: number;
  soft: number;
  block: number;
  pending: number;
  avgScore: number;
  claims: ClaimRow[];
  deleted: DeletedRow[];
  companies: string[];
};

const VERDICT_STYLE: Record<string, { bg: string; color: string; label: string }> = {
  PASS: { bg: "#ecfdf5", color: "#059669", label: "Substantiated" },
  SOFT_FLAG: { bg: "#fffbeb", color: "#d97706", label: "Flagged" },
  BLOCK: { bg: "#fef2f2", color: "#dc2626", label: "Blocked" },
  PENDING: { bg: "#f8fafc", color: "#64748b", label: "Pending" },
};

const inputStyle: React.CSSProperties = {
  height: 32, padding: "0 10px", borderRadius: 8, fontSize: 12,
  border: "1px solid var(--border-subtle)", background: "var(--bg-tertiary)",
  color: "var(--text-primary)", outline: "none", cursor: "pointer",
};

export function ReportClient({ data }: { data: ReportData }) {
  const reportRef = useRef<HTMLDivElement>(null);
  const [filterVerdict, setFilterVerdict] = useState<string>("ALL");
  const [companyFilter, setCompanyFilter] = useState("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [showDeleted, setShowDeleted] = useState(false);
  const [generating, setGenerating] = useState(false);

  const filtered = useMemo(() => {
    return data.claims.filter((c) => {
      if (filterVerdict !== "ALL" && c.verdict !== filterVerdict) return false;
      if (companyFilter !== "all" && c.source !== companyFilter) return false;
      if (dateFrom && c.createdAt < dateFrom) return false;
      if (dateTo && c.createdAt > dateTo + "T23:59:59") return false;
      return true;
    });
  }, [data.claims, filterVerdict, companyFilter, dateFrom, dateTo]);

  const filteredDeleted = useMemo(() => {
    return data.deleted.filter((d) => {
      if (companyFilter !== "all" && d.source !== companyFilter) return false;
      if (dateFrom && d.deletedAt < dateFrom) return false;
      if (dateTo && d.deletedAt > dateTo + "T23:59:59") return false;
      return true;
    });
  }, [data.deleted, companyFilter, dateFrom, dateTo]);

  const hasFilters = companyFilter !== "all" || dateFrom || dateTo || filterVerdict !== "ALL";

  // Recompute KPIs from filtered
  const fPass = filtered.filter((c) => c.verdict === "PASS").length;
  const fSoft = filtered.filter((c) => c.verdict === "SOFT_FLAG").length;
  const fBlock = filtered.filter((c) => c.verdict === "BLOCK").length;
  const fPending = filtered.filter((c) => c.verdict === "PENDING").length;
  const fAvg = filtered.length > 0 ? filtered.reduce((s, c) => s + c.score, 0) / filtered.length : 0;

  async function generatePDF() {
    setGenerating(true);
    const now = new Date().toLocaleString();
    const deletedSection = filteredDeleted.length > 0 ? `
      <div class="section-title">🗑 Deleted Claims Audit (${filteredDeleted.length} records)</div>
      <table><thead><tr><th>#</th><th>CT-ID</th><th style="width:35%">Claim Text</th><th>Last Verdict</th><th>Score</th><th>Deleted At</th></tr></thead>
      <tbody>${filteredDeleted.map((d, i) => {
        const vs = d.verdict === "PASS" ? "pass" : d.verdict === "SOFT_FLAG" ? "soft" : d.verdict === "BLOCK" ? "block" : "pending";
        return `<tr><td class="mono">${i+1}</td><td class="mono">${d.ctId}</td><td>${d.text}</td><td><span class="badge badge-${vs}">${VERDICT_STYLE[d.verdict]?.label ?? d.verdict}</span></td><td class="mono">${Math.round(d.score * 100)}%</td><td class="mono">${new Date(d.deletedAt).toLocaleDateString()}</td></tr>`;
      }).join("")}</tbody></table>` : "";

    const html = `<!DOCTYPE html><html><head>
      <title>Revisto Claim Substantiation Report</title>
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
      <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family:'Inter',system-ui,sans-serif; color:#1e293b; padding:40px; font-size:11px; }
        .header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:30px; border-bottom:2px solid #FF5F6D; padding-bottom:16px; }
        .header h1 { font-size:22px; font-weight:800; letter-spacing:-0.03em; }
        .header p { font-size:11px; color:#64748b; }
        .date { font-size:10px; color:#94a3b8; text-align:right; }
        .kpi-row { display:grid; grid-template-columns:repeat(5,1fr); gap:12px; margin-bottom:24px; }
        .kpi { padding:12px; border:1px solid #e8ecf1; border-radius:8px; text-align:center; }
        .kpi .value { font-size:22px; font-weight:800; }
        .kpi .label { font-size:9px; color:#94a3b8; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:4px; }
        .kpi.pass .value{color:#10b981} .kpi.soft .value{color:#f59e0b} .kpi.block .value{color:#ef4444} .kpi.pending .value{color:#94a3b8} .kpi.total .value{color:#6366f1}
        table { width:100%; border-collapse:collapse; margin-top:16px; }
        th { text-align:left; font-size:9px; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.06em; padding:8px 10px; border-bottom:2px solid #e8ecf1; }
        td { padding:8px 10px; border-bottom:1px solid #f1f5f9; font-size:10px; vertical-align:top; }
        tr:nth-child(even){background:#fafafa}
        .badge{display:inline-block;padding:2px 8px;border-radius:99px;font-size:9px;font-weight:600}
        .badge-pass{background:#ecfdf5;color:#059669} .badge-soft{background:#fffbeb;color:#d97706} .badge-block{background:#fef2f2;color:#dc2626} .badge-pending{background:#f8fafc;color:#64748b}
        .mono{font-family:'JetBrains Mono',monospace;font-size:10px}
        .section-title{font-size:13px;font-weight:700;color:#1e293b;margin:24px 0 8px;display:flex;align-items:center;gap:6px}
        .footer{margin-top:30px;padding-top:12px;border-top:1px solid #e8ecf1;font-size:9px;color:#94a3b8;display:flex;justify-content:space-between}
        @media print{body{padding:20px}}
      </style>
    </head><body>
      <div class="header">
        <div><h1>Revisto · Claim Substantiation Report</h1><p>Evidence substantiation pipeline results — Requirements v1.1</p></div>
        <div class="date">Generated: ${now}<br/>Filter: ${companyFilter === "all" ? "All Companies" : companyFilter} · ${filterVerdict === "ALL" ? "All Verdicts" : VERDICT_STYLE[filterVerdict]?.label ?? filterVerdict}</div>
      </div>
      <div class="kpi-row">
        <div class="kpi total"><p class="label">Active</p><p class="value">${filtered.length}</p></div>
        <div class="kpi pass"><p class="label">Substantiated</p><p class="value">${fPass}</p></div>
        <div class="kpi soft"><p class="label">Flagged</p><p class="value">${fSoft}</p></div>
        <div class="kpi block"><p class="label">Blocked</p><p class="value">${fBlock}</p></div>
        <div class="kpi pending"><p class="label">Deleted</p><p class="value">${filteredDeleted.length}</p></div>
      </div>
      <p style="font-size:11px;color:#64748b;margin-bottom:16px">Average Coverage Score: <strong style="color:#FF5F6D">${Math.round(fAvg * 100)}%</strong></p>
      <div class="section-title">Claims Detail (${filtered.length} records)</div>
      <table><thead><tr><th>#</th><th>CT-ID</th><th style="width:35%">Claim Text</th><th>Company</th><th>Verdict</th><th>Score</th><th>Reasoning</th></tr></thead>
      <tbody>${filtered.map((c, i) => {
        const vs = c.verdict === "PASS" ? "pass" : c.verdict === "SOFT_FLAG" ? "soft" : c.verdict === "BLOCK" ? "block" : "pending";
        const label = VERDICT_STYLE[c.verdict]?.label ?? c.verdict;
        const reason = c.reasoning ? c.reasoning.slice(0, 200) + (c.reasoning.length > 200 ? "…" : "") : "—";
        return `<tr><td class="mono">${i+1}</td><td class="mono">${c.ctId}</td><td>${c.text}</td><td>${c.source || "—"}</td><td><span class="badge badge-${vs}">${label}</span></td><td class="mono">${Math.round(c.score * 100)}%</td><td>${reason}</td></tr>`;
      }).join("")}</tbody></table>
      ${deletedSection}
      <div class="footer"><span>Revisto · Claim Substantiation Pipeline · Requirements v1.1</span><span>Confidential — Internal Use Only</span></div>
    </body></html>`;

    const iframe = document.createElement("iframe");
    iframe.style.cssText = "position:fixed;top:-9999px;left:-9999px;width:0;height:0;";
    document.body.appendChild(iframe);
    iframe.contentDocument!.open();
    iframe.contentDocument!.write(html);
    iframe.contentDocument!.close();
    setTimeout(() => {
      iframe.contentWindow!.focus();
      iframe.contentWindow!.print();
      setTimeout(() => { document.body.removeChild(iframe); setGenerating(false); }, 1000);
    }, 700);
  }

  return (
    <div style={{ padding: "28px 36px" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.02em", marginBottom: 4 }}>Report</h1>
          <p style={{ fontSize: 14, color: "var(--text-muted)" }}>
            {data.total} active · {data.deleted.length} deleted · all substantiation results
          </p>
        </div>
        <button onClick={generatePDF} disabled={generating} className="btn-accent" style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13 }}>
          {generating ? (
            <><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: "dna-rotate 1s linear infinite" }}><path d="M21 12a9 9 0 11-6.219-8.56"/></svg>Generating…</>
          ) : (
            <><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><path d="M12 11v6M9 14l3 3 3-3"/></svg>Generate PDF</>
          )}
        </button>
      </div>

      {/* Filter Bar */}
      <div className="glass-card-static" style={{ padding: "12px 16px", marginBottom: 16, display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2">
          <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
        </svg>

        {/* Company */}
        <select value={companyFilter} onChange={(e) => setCompanyFilter(e.target.value)} style={inputStyle}>
          <option value="all">All Companies</option>
          {data.companies.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>

        {/* Verdict */}
        <select value={filterVerdict} onChange={(e) => setFilterVerdict(e.target.value)} style={inputStyle}>
          <option value="ALL">All Verdicts</option>
          {["PASS", "SOFT_FLAG", "BLOCK", "PENDING"].map((v) => (
            <option key={v} value={v}>{VERDICT_STYLE[v]?.label ?? v}</option>
          ))}
        </select>

        {/* Date range */}
        <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} style={{ ...inputStyle, width: 130 }} />
        <span style={{ fontSize: 11, color: "var(--text-muted)" }}>→</span>
        <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} style={{ ...inputStyle, width: 130 }} />

        {hasFilters && (
          <button onClick={() => { setCompanyFilter("all"); setFilterVerdict("ALL"); setDateFrom(""); setDateTo(""); }}
            style={{ height: 32, padding: "0 12px", borderRadius: 8, fontSize: 11, fontWeight: 600, border: "1px solid var(--border-subtle)", background: "transparent", color: "var(--text-muted)", cursor: "pointer" }}>
            ✕ Clear
          </button>
        )}

        <span style={{ marginLeft: "auto", fontSize: 11, color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}>
          {filtered.length} active · {filteredDeleted.length} deleted
        </span>
      </div>

      {/* KPI Summary */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 12, marginBottom: 20 }}>
        {[
          { label: "Active", value: filtered.length, color: "#6366f1" },
          { label: "Substantiated", value: fPass, color: "#10b981" },
          { label: "Flagged", value: fSoft, color: "#f59e0b" },
          { label: "Blocked", value: fBlock, color: "#ef4444" },
          { label: "Pending", value: fPending, color: "#94a3b8" },
          { label: "Deleted", value: filteredDeleted.length, color: "#64748b" },
        ].map(({ label, value, color }) => (
          <div key={label} className="glass-card-static" style={{ padding: "14px 16px", textAlign: "center" }}>
            <p style={{ fontSize: 10, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 6 }}>{label}</p>
            <p style={{ fontSize: 24, fontWeight: 800, color }}>{value}</p>
          </div>
        ))}
      </div>

      {/* Avg coverage bar */}
      <div className="glass-card-static" style={{ padding: "12px 16px", marginBottom: 20 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
          <div>
            <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>Average Coverage Score</span>
            <p style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>
              Sum of all claim evidence coverage scores (0–100%) ÷ number of substantiated claims
            </p>
          </div>
          <div style={{ textAlign: "right" }}>
            <span className="gradient-text" style={{ fontSize: 18, fontWeight: 800 }}>{Math.round(fAvg * 100)}%</span>
            <p style={{ fontSize: 9, color: fAvg >= 0.8 ? "#10b981" : fAvg >= 0.6 ? "#f59e0b" : "#ef4444", fontWeight: 600, textTransform: "uppercase", marginTop: 2 }}>
              {fAvg >= 0.8 ? "✓ Strong" : fAvg >= 0.6 ? "⚠ Moderate" : "✗ Weak"}
            </p>
          </div>
        </div>
        <div className="score-bar-track">
          <div className={`score-bar-fill ${fAvg >= 0.8 ? "pass" : fAvg >= 0.6 ? "soft" : "block"}`} style={{ width: `${Math.round(fAvg * 100)}%` }} />
        </div>
        <div style={{ position: "relative", height: 14, marginTop: 4 }}>
          <span style={{ position: "absolute", left: "60%", fontSize: 8, color: "var(--text-muted)", transform: "translateX(-50%)" }}>60% MLR min</span>
          <span style={{ position: "absolute", left: "80%", fontSize: 8, color: "var(--text-muted)", transform: "translateX(-50%)" }}>80% target</span>
        </div>
      </div>

      {/* Active Claims Table */}
      <div ref={reportRef} className="glass-card-static" style={{ overflow: "hidden", marginBottom: 16 }}>
        <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border-subtle)", background: "var(--bg-tertiary)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <h2 style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
            Active Claims ({filtered.length})
          </h2>
        </div>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              {["#", "CT-ID", "Company", "Claim Text", "Verdict", "Score", "Reasoning"].map((h) => (
                <th key={h} style={{ textAlign: "left", padding: "12px 14px", fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", borderBottom: "2px solid var(--border-subtle)", background: "var(--bg-tertiary)" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.length > 0 ? filtered.map((c, i) => {
              const vs = VERDICT_STYLE[c.verdict] ?? VERDICT_STYLE.PENDING;
              return (
                <tr key={c.id}>
                  <td style={{ padding: "10px 14px", borderBottom: "1px solid var(--border-subtle)", fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>{i + 1}</td>
                  <td style={{ padding: "10px 14px", borderBottom: "1px solid var(--border-subtle)", fontSize: 11, fontFamily: "var(--font-mono)", color: "#818cf8" }}>{c.ctId}</td>
                  <td style={{ padding: "10px 14px", borderBottom: "1px solid var(--border-subtle)", fontSize: 11, color: "var(--text-muted)" }}>{c.source || "—"}</td>
                  <td style={{ padding: "10px 14px", borderBottom: "1px solid var(--border-subtle)", fontSize: 12, color: "var(--text-primary)", maxWidth: 300 }}>{c.text.length > 90 ? c.text.slice(0, 90) + "…" : c.text}</td>
                  <td style={{ padding: "10px 14px", borderBottom: "1px solid var(--border-subtle)" }}>
                    <span style={{ display: "inline-block", padding: "3px 10px", borderRadius: 99, fontSize: 10, fontWeight: 600, background: vs.bg, color: vs.color }}>{vs.label}</span>
                  </td>
                  <td style={{ padding: "10px 14px", borderBottom: "1px solid var(--border-subtle)", fontFamily: "var(--font-mono)", fontSize: 12, fontWeight: 600, color: "var(--text-primary)" }}>{Math.round(c.score * 100)}%</td>
                  <td style={{ padding: "10px 14px", borderBottom: "1px solid var(--border-subtle)", fontSize: 11, color: "var(--text-muted)", maxWidth: 280, lineHeight: 1.4 }}>
                    {c.reasoning ? (c.reasoning.length > 110 ? c.reasoning.slice(0, 110) + "…" : c.reasoning) : "—"}
                  </td>
                </tr>
              );
            }) : (
              <tr><td colSpan={7} style={{ padding: "40px 14px", textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>No claims match the current filters.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Deleted Claims Audit Table */}
      <div className="glass-card-static" style={{ overflow: "hidden", marginBottom: 16 }}>
        <div
          onClick={() => setShowDeleted(!showDeleted)}
          style={{ padding: "12px 16px", borderBottom: showDeleted ? "1px solid var(--border-subtle)" : "none", background: "var(--bg-tertiary)", display: "flex", alignItems: "center", justifyContent: "space-between", cursor: "pointer" }}
        >
          <h2 style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ fontSize: 13 }}>🗑</span> Deleted Claims Audit ({filteredDeleted.length})
          </h2>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2" style={{ transform: showDeleted ? "rotate(180deg)" : "none", transition: "transform 0.2s" }}>
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>

        {showDeleted && (
          filteredDeleted.length > 0 ? (
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  {["#", "CT-ID", "Company", "Claim Text", "Last Verdict", "Score", "Deleted At"].map((h) => (
                    <th key={h} style={{ textAlign: "left", padding: "12px 14px", fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", borderBottom: "2px solid var(--border-subtle)", background: "var(--bg-tertiary)" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredDeleted.map((d, i) => {
                  const vs = VERDICT_STYLE[d.verdict] ?? VERDICT_STYLE.PENDING;
                  return (
                    <tr key={d.id} style={{ opacity: 0.75 }}>
                      <td style={{ padding: "10px 14px", borderBottom: "1px solid var(--border-subtle)", fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>{i + 1}</td>
                      <td style={{ padding: "10px 14px", borderBottom: "1px solid var(--border-subtle)", fontSize: 11, fontFamily: "var(--font-mono)", color: "#818cf8" }}>{d.ctId}</td>
                      <td style={{ padding: "10px 14px", borderBottom: "1px solid var(--border-subtle)", fontSize: 11, color: "var(--text-muted)" }}>{d.source || "—"}</td>
                      <td style={{ padding: "10px 14px", borderBottom: "1px solid var(--border-subtle)", fontSize: 12, color: "var(--text-secondary)", maxWidth: 300 }}>{d.text.length > 90 ? d.text.slice(0, 90) + "…" : d.text}</td>
                      <td style={{ padding: "10px 14px", borderBottom: "1px solid var(--border-subtle)" }}>
                        <span style={{ display: "inline-block", padding: "3px 10px", borderRadius: 99, fontSize: 10, fontWeight: 600, background: vs.bg, color: vs.color }}>{vs.label}</span>
                      </td>
                      <td style={{ padding: "10px 14px", borderBottom: "1px solid var(--border-subtle)", fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--text-muted)" }}>{Math.round(d.score * 100)}%</td>
                      <td style={{ padding: "10px 14px", borderBottom: "1px solid var(--border-subtle)", fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                        {new Date(d.deletedAt).toLocaleDateString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            <div style={{ padding: "30px 16px", textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>
              No deleted claims recorded yet. Future deletions will appear here.
            </div>
          )
        )}
      </div>

      {/* Footer */}
      <div style={{ marginTop: 8, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <p style={{ fontSize: 11, color: "var(--text-muted)" }}>Revisto Substantiation Pipeline · Requirements v1.1 · Confidential</p>
        <p style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>Avg Coverage: {Math.round(fAvg * 100)}%</p>
      </div>
    </div>
  );
}
