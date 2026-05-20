"use client";

import { useEffect, useState } from "react";

const STEPS = [
  {
    id: 1,
    label: "Claim Input",
    description: "Promotional claim text + CT-ID classification",
    detail: "Each pharmaceutical promotional claim is ingested alongside its Claim Type ID (CT-ID), which determines permissible reference types and tier weights. The CT-ID classification (e.g., CT-301 for efficacy, CT-601 for safety) drives the entire downstream decision framework — controlling which evidence sources are acceptable and how heavily each tier contributes to the coverage score.",
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
      </svg>
    ),
    color: "#6366f1",
    bg: "#eef2ff",
    darkBg: "rgba(99,102,241,0.12)",
  },
  {
    id: 2,
    label: "Query Rewriting",
    description: "GPT-5.2 rewrites into PubMed-style search queries",
    detail: "The raw promotional claim is transformed by GPT-5.2 into 3–5 PubMed-style search queries optimized for biomedical retrieval. This step extracts key entities (drug names, endpoints, populations), resolves INN↔Brand equivalences (e.g., efgartigimod PH20 → VYVGART Hytrulo), and generates boolean AND-match keyword lists for high-precision recall.",
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
      </svg>
    ),
    color: "#8b5cf6",
    bg: "#f5f3ff",
    darkBg: "rgba(139,92,246,0.12)",
  },
  {
    id: 3,
    label: "3-Signal Retrieval",
    description: "MedCPT Dense + BM25 Sparse + AND-match Keywords",
    detail: "Three independent retrieval signals are fired simultaneously: (1) MedCPT Dense Encoder — a biomedical-specific transformer that captures semantic meaning across 4,776 indexed passages, returning Top-150 candidates; (2) BM25 Sparse — lexical matching via Qdrant's built-in BM25 returning Top-100; (3) AND-match Keywords — exact keyword co-occurrence for high-precision anchoring returning Top-20.",
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8"/>
        <path d="M21 21l-4.35-4.35"/>
        <path d="M11 8v6M8 11h6"/>
      </svg>
    ),
    color: "#FF5F6D",
    bg: "#fff5f5",
    darkBg: "rgba(255,95,109,0.12)",
  },
  {
    id: 4,
    label: "RRF Fusion",
    description: "Reciprocal Rank Fusion → Diversity Cap → Tier Boost",
    detail: "All three retrieval signals are merged using Reciprocal Rank Fusion (RRF) with weights: Dense 50%, BM25 25%, AND-match 25%. Post-fusion, a Diversity Cap limits each reference source to max 5 chunks, an Off-product PI Penalty deprioritizes irrelevant product labels, and Tier Boost elevates Tier P (primary) references. The top 15 passages advance to the judge.",
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
      </svg>
    ),
    color: "#f59e0b",
    bg: "#fffbeb",
    darkBg: "rgba(245,158,11,0.12)",
  },
  {
    id: 5,
    label: "LLM Judge",
    description: "Claude Sonnet evaluates against Revisto v1.1 requirements",
    detail: "Claude Sonnet 4 acts as the final adjudicator, evaluating each claim against all 10 Revisto v1.1 requirements simultaneously. It checks PICOT alignment, numeric tolerance (±2–5%), table/figure anchoring, source locatability, and non-duplicative support. The judge outputs a structured verdict (PASS / SOFT_FLAG / BLOCK) with a coverage score, reasoning chain, and specific evidence anchors.",
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        <path d="M9 12l2 2 4-4"/>
      </svg>
    ),
    color: "#10b981",
    bg: "#ecfdf5",
    darkBg: "rgba(16,185,129,0.12)",
  },
  {
    id: 6,
    label: "Verdict",
    description: "PASS / SOFT FLAG / BLOCK with evidence passages",
    detail: "The final substantiation verdict is recorded with full traceability: the coverage score (0–100%), specific evidence passages with page-level anchors, the judge's reasoning chain, and any requirement violations. Results are stored in the database and can be overridden by human reviewers when additional context is available.",
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
        <polyline points="22 4 12 14.01 9 11.01"/>
      </svg>
    ),
    color: "#059669",
    bg: "#ecfdf5",
    darkBg: "rgba(5,150,105,0.12)",
  },
  {
    id: 7,
    label: "Agent Self-Critic",
    description: "Coming Soon — Autonomous review of BLOCK verdicts",
    detail: "A future autonomous agent that re-examines every BLOCK verdict by performing a deeper, targeted search against the full document corpus. The self-critic agent will challenge the original judge's reasoning, attempt alternative query reformulations, consider cross-reference evidence, and either confirm the BLOCK or escalate with a revised recommendation. This creates a closed-loop quality assurance system that minimizes false negatives.",
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="5" y="8" width="14" height="12" rx="2"/>
        <path d="M12 8V5"/>
        <circle cx="12" cy="3" r="2"/>
        <circle cx="9" cy="13" r="1" fill="currentColor"/>
        <circle cx="15" cy="13" r="1" fill="currentColor"/>
        <path d="M9 17h6"/>
        <path d="M3 14h2M19 14h2"/>
      </svg>
    ),
    color: "#a855f7",
    bg: "#faf5ff",
    darkBg: "rgba(168,85,247,0.12)",
    isFuture: true,
  },
];

export default function HowItWorksPage() {
  const [activeStep, setActiveStep] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    if (isPaused) return;
    const interval = setInterval(() => {
      setActiveStep((s) => (s + 1) % STEPS.length);
    }, 3000);
    return () => clearInterval(interval);
  }, [isPaused]);

  return (
    <div style={{ padding: "28px 36px" }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.02em", marginBottom: 4 }}>
          How It Works
        </h1>
        <p style={{ fontSize: 14, color: "var(--text-muted)" }}>
          End-to-end claim substantiation pipeline — from input to verdict
        </p>
      </div>

      {/* Animated Pipeline */}
      <div className="glass-card-static" style={{ padding: 28, marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
          <h2 style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
            Pipeline Flow
          </h2>
          <button
            onClick={() => setIsPaused((p) => !p)}
            style={{
              padding: "4px 12px", borderRadius: 6, border: "1px solid var(--border-subtle)",
              background: "var(--bg-tertiary)", color: "var(--text-secondary)", fontSize: 11,
              cursor: "pointer", display: "flex", alignItems: "center", gap: 5,
            }}
          >
            {isPaused ? (
              <><svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21"/></svg> Play</>
            ) : (
              <><svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg> Pause</>
            )}
          </button>
        </div>

        <div style={{ display: "flex", alignItems: "flex-start", gap: 0 }}>
          {STEPS.map((step, i) => {
            const isActive = i === activeStep;
            const isDone = i < activeStep;
            const isFuture = (step as any).isFuture;

            return (
              <div
                key={step.id}
                style={{
                  flex: 1,
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  position: "relative",
                  cursor: "pointer",
                  opacity: isFuture && !isActive ? 0.5 : 1,
                  transition: "opacity 0.3s",
                }}
                onClick={() => { setActiveStep(i); setIsPaused(true); }}
              >
                {/* Connector */}
                {i > 0 && (
                  <div style={{
                    position: "absolute", top: 22, right: "50%", width: "100%", height: 2, zIndex: 0,
                  }}>
                    <div style={{
                      height: "100%",
                      background: isDone || isActive ? `${step.color}30` : "var(--border-subtle)",
                      transition: "background 0.6s ease",
                    }} />
                  </div>
                )}

                {/* Icon */}
                <div
                  style={{
                    width: 44, height: 44, borderRadius: 12,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    background: isActive ? step.bg : "var(--bg-tertiary)",
                    border: `2px solid ${isActive ? step.color : isDone ? step.color + "50" : "var(--border-subtle)"}`,
                    color: isActive ? step.color : isDone ? step.color : "var(--text-muted)",
                    transition: "all 0.5s cubic-bezier(0.16, 1, 0.3, 1)",
                    transform: isActive ? "scale(1.15)" : "scale(1)",
                    boxShadow: isActive ? `0 4px 20px ${step.color}20` : "none",
                    position: "relative", zIndex: 1,
                  }}
                >
                  {step.icon}
                  {isFuture && (
                    <div style={{
                      position: "absolute", top: -6, right: -6, width: 18, height: 18, borderRadius: "50%",
                      background: "#a855f7", color: "#fff", fontSize: 8, fontWeight: 700,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      border: "2px solid var(--bg-card)",
                    }}>
                      ✦
                    </div>
                  )}
                </div>

                {/* Label */}
                <p style={{
                  fontSize: 10, fontWeight: isActive ? 700 : 500,
                  color: isActive ? step.color : "var(--text-muted)",
                  marginTop: 8, textAlign: "center", transition: "all 0.3s",
                  lineHeight: 1.3, maxWidth: 80,
                }}>
                  {step.label}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Active Step Detail */}
      <div className="glass-card" style={{ padding: 24, marginBottom: 20, transition: "all 0.3s" }}>
        <div style={{ display: "flex", gap: 16, alignItems: "flex-start" }}>
          <div style={{
            width: 52, height: 52, borderRadius: 14, flexShrink: 0,
            display: "flex", alignItems: "center", justifyContent: "center",
            background: STEPS[activeStep].bg, color: STEPS[activeStep].color,
            border: `2px solid ${STEPS[activeStep].color}40`,
          }}>
            {STEPS[activeStep].icon}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
              <span style={{
                fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 99,
                background: STEPS[activeStep].color + "15", color: STEPS[activeStep].color,
                fontFamily: "var(--font-mono)",
              }}>
                Step {STEPS[activeStep].id}
              </span>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: "var(--text-primary)" }}>
                {STEPS[activeStep].label}
              </h3>
              {(STEPS[activeStep] as any).isFuture && (
                <span style={{
                  fontSize: 9, fontWeight: 700, padding: "2px 8px", borderRadius: 99,
                  background: "#faf5ff", color: "#a855f7", border: "1px solid #e9d5ff",
                }}>
                  COMING SOON
                </span>
              )}
            </div>
            <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 10, fontWeight: 500 }}>
              {STEPS[activeStep].description}
            </p>
            <p style={{ fontSize: 12, color: "var(--text-muted)", lineHeight: 1.7 }}>
              {STEPS[activeStep].detail}
            </p>
          </div>
        </div>
      </div>

      {/* All Steps Grid */}
      <h2 style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 12 }}>
        All Pipeline Steps
      </h2>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        {STEPS.map((step, i) => {
          const isFuture = (step as any).isFuture;
          return (
            <div
              key={step.id}
              className="glass-card"
              onClick={() => { setActiveStep(i); setIsPaused(true); window.scrollTo({ top: 0, behavior: "smooth" }); }}
              style={{
                padding: 18, cursor: "pointer", opacity: isFuture ? 0.7 : 1,
                borderLeft: `3px solid ${step.color}`,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                <div style={{
                  width: 32, height: 32, borderRadius: 8,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  background: step.bg, color: step.color,
                }}>
                  {step.icon}
                </div>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span style={{ fontSize: 10, fontWeight: 700, color: step.color, fontFamily: "var(--font-mono)" }}>
                      Step {step.id}
                    </span>
                    {isFuture && (
                      <span style={{ fontSize: 8, fontWeight: 700, padding: "1px 5px", borderRadius: 99, background: "#faf5ff", color: "#a855f7" }}>
                        FUTURE
                      </span>
                    )}
                  </div>
                  <p style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>{step.label}</p>
                </div>
              </div>
              <p style={{ fontSize: 11, color: "var(--text-muted)", lineHeight: 1.5 }}>{step.description}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
