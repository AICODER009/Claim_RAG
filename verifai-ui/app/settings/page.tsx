"use client";

import { useTheme } from "@/components/ThemeProvider";

const REQUIREMENTS = [
  { id: "1.1", title: "Claim-Type-Driven Decision Framework", desc: "Each claim mapped to CT-ID determining permissible reference types and tier weights." },
  { id: "1.2", title: "Non-Duplicative Reference Support", desc: "Each reference contributes unique support. Per-source diversity cap of 5 chunks." },
  { id: "2.1", title: "Table & Figure Anchoring", desc: "Anchors must include derived data points with structural context." },
  { id: "2.2", title: "Source Locatability", desc: "Source text locatable via file name, page number, section heading, and sentence index." },
  { id: "2.3", title: "PICOT Alignment", desc: "Population, Intervention, Comparator, Outcome, Timeframe must align." },
  { id: "3.1", title: "Numeric Tolerance ±2–5%", desc: "±2% for percentages, ±5% for absolute values." },
  { id: "3.2", title: "CONSORT n(X%) Format", desc: "Clinical paper 'n (X%)' equivalent to plain 'X%' per ICH E3." },
  { id: "3.3", title: "Simple Arithmetic", desc: "If verifiable by simple arithmetic from same passage, accepted." },
  { id: "4.1", title: "INN ↔ Brand Equivalence", desc: "INN names (efgartigimod PH20) treated as equivalent to brand names (VYVGART Hytrulo)." },
  { id: "4.2", title: "Scale Disambiguation", desc: "I-RODS, INCAT, ONLS, MRC and aINCAT have explicit direction reference." },
];

const MODELS = [
  { label: "Query Rewriter", model: "GPT-5.2", provider: "OpenAI", icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg> },
  { label: "Judge", model: "claude-sonnet-4-6", provider: "Anthropic", icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg> },
  { label: "Query Encoder", model: "MedCPT-Query-Encoder", provider: "Local (HuggingFace)", icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg> },
  { label: "BM25 Sparse", model: "Qdrant/bm25", provider: "Local (fastembed)", icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg> },
];

const RETRIEVAL = [
  { label: "Dense (MedCPT)", weight: 50, topK: 150, color: "#FF5F6D" },
  { label: "BM25 Sparse", weight: 25, topK: 100, color: "#FF8A65" },
  { label: "AND-match Keywords", weight: 25, topK: 20, color: "#f59e0b" },
];

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();

  return (
    <div style={{ padding: "28px 36px" }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.02em", marginBottom: 4 }}>
          Settings
        </h1>
        <p style={{ fontSize: 14, color: "var(--text-muted)" }}>
          Pipeline configuration, appearance, and substantiation requirements
        </p>
      </div>

      {/* Two-column grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 20, alignItems: "stretch" }}>

        {/* Appearance Card */}
        <div className="glass-card-static" style={{ padding: 22 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 20 }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-coral)" strokeWidth="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
            <h2 style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)" }}>Appearance</h2>
          </div>

          {/* Pill-shaped Day / Night toggle */}
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {/* DAY MODE pill */}
            <button
              onClick={() => setTheme("light")}
              style={{
                display: "flex", alignItems: "center", justifyContent: "space-between",
                width: "100%", padding: "0 6px 0 20px", height: 52, borderRadius: 99,
                border: theme === "light" ? "2px solid #e5e7eb" : "1px solid var(--border-subtle)",
                background: theme === "light" ? "#f3f4f6" : "var(--bg-tertiary)",
                cursor: "pointer", transition: "all 0.25s",
              }}
            >
              <span style={{ fontSize: 13, fontWeight: 700, letterSpacing: "0.06em", color: theme === "light" ? "#111" : "var(--text-muted)", textTransform: "uppercase" }}>
                Day Mode
              </span>
              <div style={{
                width: 42, height: 42, borderRadius: "50%",
                background: theme === "light" ? "#fff" : "var(--bg-secondary)",
                border: theme === "light" ? "1.5px solid #e5e7eb" : "1px solid var(--border-subtle)",
                display: "flex", alignItems: "center", justifyContent: "center",
                boxShadow: theme === "light" ? "0 2px 8px rgba(0,0,0,0.08)" : "none",
                transition: "all 0.25s",
              }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={theme === "light" ? "#f59e0b" : "var(--text-muted)"} strokeWidth="1.8">
                  <circle cx="12" cy="12" r="5"/>
                  <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
                </svg>
              </div>
            </button>

            {/* NIGHT MODE pill */}
            <button
              onClick={() => setTheme("dark")}
              style={{
                display: "flex", alignItems: "center", justifyContent: "space-between",
                width: "100%", padding: "0 20px 0 6px", height: 52, borderRadius: 99,
                border: "none",
                background: theme === "dark" ? "#111" : "var(--bg-tertiary)",
                cursor: "pointer", transition: "all 0.25s",
              }}
            >
              <div style={{
                width: 42, height: 42, borderRadius: "50%",
                background: theme === "dark" ? "#1e1e28" : "var(--bg-secondary)",
                border: theme === "dark" ? "1.5px solid #333" : "1px solid var(--border-subtle)",
                display: "flex", alignItems: "center", justifyContent: "center",
                transition: "all 0.25s",
              }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={theme === "dark" ? "#c4b5fd" : "var(--text-muted)"} strokeWidth="1.8">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
                  <path d="M17 3l1 2M19 7l2-1" strokeLinecap="round"/>
                </svg>
              </div>
              <span style={{ fontSize: 13, fontWeight: 700, letterSpacing: "0.06em", color: theme === "dark" ? "#fff" : "var(--text-muted)", textTransform: "uppercase" }}>
                Night Mode
              </span>
            </button>
          </div>
        </div>

        {/* Pipeline Info Card */}
        <div className="glass-card-static" style={{ padding: 22 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-coral)" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
            <h2 style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)" }}>Pipeline Summary</h2>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
              <span style={{ color: "var(--text-muted)" }}>Total indexed passages</span>
              <span style={{ fontWeight: 600, color: "var(--text-primary)", fontFamily: "var(--font-mono)" }}>4,776</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
              <span style={{ color: "var(--text-muted)" }}>Reference documents</span>
              <span style={{ fontWeight: 600, color: "var(--text-primary)", fontFamily: "var(--font-mono)" }}>35</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
              <span style={{ color: "var(--text-muted)" }}>Claim types (CT-IDs)</span>
              <span style={{ fontWeight: 600, color: "var(--text-primary)", fontFamily: "var(--font-mono)" }}>15</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
              <span style={{ color: "var(--text-muted)" }}>Requirements version</span>
              <span style={{ fontWeight: 600, color: "var(--accent-coral)", fontFamily: "var(--font-mono)" }}>v1.1</span>
            </div>
          </div>
          <div style={{
            marginTop: 14, padding: "10px 12px", borderRadius: 8,
            background: theme === "dark" ? "rgba(255,95,109,0.06)" : "#fff5f5",
            border: theme === "dark" ? "1px solid rgba(255,95,109,0.12)" : "1px solid #fecaca",
            fontSize: 11, color: "var(--text-secondary)", lineHeight: 1.5,
          }}>
            <strong style={{ color: "var(--accent-coral)" }}>Flow: </strong>
            Dense + BM25 + AND-match → RRF → Diversity Cap → PI Penalty → Tier Boost → Top 15 → Judge
          </div>
        </div>
      </div>

      {/* AI Models */}
      <div className="glass-card-static" style={{ padding: 22, marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-coral)" strokeWidth="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
          <h2 style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)" }}>AI Models</h2>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
          {MODELS.map((m) => (
            <div key={m.label} style={{
              padding: 14, borderRadius: 10, background: "var(--bg-tertiary)", border: "1px solid var(--border-subtle)",
              display: "flex", flexDirection: "column", gap: 6,
            }}>
              <div style={{ color: "var(--accent-coral)" }}>{m.icon}</div>
              <p style={{ fontSize: 10, fontWeight: 500, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>{m.label}</p>
              <p style={{ fontSize: 14, fontWeight: 700, color: "var(--text-primary)" }}>{m.model}</p>
              <p style={{ fontSize: 11, color: "var(--text-muted)" }}>{m.provider}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Retrieval Architecture */}
      <div className="glass-card-static" style={{ padding: 22, marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-coral)" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
          <h2 style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)" }}>Retrieval Architecture (RRF Fusion)</h2>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
          {RETRIEVAL.map((r) => (
            <div key={r.label} style={{
              padding: 16, borderRadius: 10, background: "var(--bg-tertiary)", border: "1px solid var(--border-subtle)",
              textAlign: "center",
            }}>
              <p className="gradient-text" style={{ fontSize: 28, fontWeight: 800, marginBottom: 4 }}>{r.weight}%</p>
              <p style={{ fontSize: 12, fontWeight: 600, color: "var(--text-primary)", marginBottom: 2 }}>{r.label}</p>
              <p style={{ fontSize: 10, color: "var(--text-muted)" }}>Top-{r.topK} candidates</p>
              {/* Weight bar */}
              <div style={{ marginTop: 10, height: 4, borderRadius: 99, background: "var(--border-subtle)", overflow: "hidden" }}>
                <div style={{ height: "100%", width: `${r.weight}%`, borderRadius: 99, background: r.color, transition: "width 0.8s ease" }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Substantiation Requirements */}
      <div className="glass-card-static" style={{ padding: 22 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-coral)" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          <h2 style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)" }}>Substantiation Requirements (Revisto v1.1)</h2>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          {REQUIREMENTS.map((req) => (
            <div key={req.id} style={{
              display: "flex", alignItems: "flex-start", gap: 10, padding: "10px 12px",
              borderRadius: 8, background: "var(--bg-tertiary)", border: "1px solid var(--border-subtle)",
            }}>
              <div style={{
                flexShrink: 0, width: 28, height: 28, borderRadius: 6,
                background: theme === "dark" ? "rgba(16,185,129,0.12)" : "#ecfdf5",
                border: theme === "dark" ? "1px solid rgba(16,185,129,0.2)" : "1px solid #a7f3d0",
                display: "flex", alignItems: "center", justifyContent: "center",
                color: "#059669", fontSize: 9, fontWeight: 700, fontFamily: "var(--font-mono)",
              }}>
                §{req.id}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ fontSize: 12, fontWeight: 600, color: "var(--text-primary)", marginBottom: 2 }}>{req.title}</p>
                <p style={{ fontSize: 10, color: "var(--text-muted)", lineHeight: 1.4 }}>{req.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
