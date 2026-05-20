"use client";

import { useEffect, useState } from "react";

const STEPS = [
  {
    id: 1,
    label: "Claim Input",
    description: "Promotional claim text + CT-ID classification",
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
  },
  {
    id: 2,
    label: "Query Rewriting",
    description: "GPT-5.2 rewrites into PubMed-style search queries",
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
      </svg>
    ),
    color: "#8b5cf6",
    bg: "#f5f3ff",
  },
  {
    id: 3,
    label: "3-Signal Retrieval",
    description: "MedCPT Dense + BM25 Sparse + AND-match Keywords",
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8"/>
        <path d="M21 21l-4.35-4.35"/>
        <path d="M11 8v6M8 11h6"/>
      </svg>
    ),
    color: "#FF5F6D",
    bg: "#fff5f5",
  },
  {
    id: 4,
    label: "RRF Fusion",
    description: "Reciprocal Rank Fusion → Diversity Cap → Tier Boost",
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
      </svg>
    ),
    color: "#f59e0b",
    bg: "#fffbeb",
  },
  {
    id: 5,
    label: "LLM Judge",
    description: "Claude Sonnet evaluates against Revisto v1.1 requirements",
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        <path d="M9 12l2 2 4-4"/>
      </svg>
    ),
    color: "#10b981",
    bg: "#ecfdf5",
  },
  {
    id: 6,
    label: "Verdict",
    description: "PASS / SOFT FLAG / BLOCK with evidence passages",
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
        <polyline points="22 4 12 14.01 9 11.01"/>
      </svg>
    ),
    color: "#059669",
    bg: "#ecfdf5",
  },
];

export function HowItWorks() {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStep((s) => (s + 1) % STEPS.length);
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="glass-card-static" style={{ padding: 24, marginBottom: 24 }}>
      <h2
        style={{
          fontSize: 11,
          fontWeight: 700,
          color: "#94a3b8",
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          marginBottom: 20,
        }}
      >
        How It Works
      </h2>

      {/* Pipeline flow */}
      <div style={{ display: "flex", alignItems: "flex-start", gap: 0 }}>
        {STEPS.map((step, i) => {
          const isActive = i === activeStep;
          const isDone = i < activeStep;

          return (
            <div
              key={step.id}
              style={{
                flex: 1,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                position: "relative",
              }}
            >
              {/* Connector line */}
              {i > 0 && (
                <div
                  style={{
                    position: "absolute",
                    top: 24,
                    right: "50%",
                    width: "100%",
                    height: 2,
                    zIndex: 0,
                  }}
                >
                  <div
                    style={{
                      height: "100%",
                      background: isDone || isActive
                        ? `linear-gradient(90deg, ${STEPS[i - 1].color}40, ${step.color}40)`
                        : "#e8ecf1",
                      transition: "background 0.8s ease",
                    }}
                  />
                  {/* Animated pulse on active connector */}
                  {isActive && (
                    <div
                      style={{
                        position: "absolute",
                        top: -3,
                        width: 8,
                        height: 8,
                        borderRadius: "50%",
                        background: step.color,
                        animation: "pulse-dot 2.5s ease infinite",
                        boxShadow: `0 0 8px ${step.color}60`,
                      }}
                    />
                  )}
                </div>
              )}

              {/* Icon circle */}
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: 14,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background: isActive ? step.bg : isDone ? step.bg : "#f8fafc",
                  border: `2px solid ${isActive ? step.color : isDone ? step.color + "60" : "#e8ecf1"}`,
                  color: isActive ? step.color : isDone ? step.color : "#94a3b8",
                  transition: "all 0.6s cubic-bezier(0.16, 1, 0.3, 1)",
                  transform: isActive ? "scale(1.1)" : "scale(1)",
                  boxShadow: isActive ? `0 4px 20px ${step.color}25` : "none",
                  position: "relative",
                  zIndex: 1,
                }}
              >
                {step.icon}
              </div>

              {/* Label */}
              <p
                style={{
                  fontSize: 11,
                  fontWeight: isActive ? 700 : 500,
                  color: isActive ? step.color : isDone ? "#475569" : "#94a3b8",
                  marginTop: 10,
                  textAlign: "center",
                  transition: "all 0.4s ease",
                  lineHeight: 1.3,
                }}
              >
                {step.label}
              </p>

              {/* Description — only show for active */}
              <p
                style={{
                  fontSize: 9,
                  color: "#94a3b8",
                  textAlign: "center",
                  marginTop: 4,
                  maxWidth: 110,
                  lineHeight: 1.4,
                  opacity: isActive ? 1 : 0,
                  transform: isActive ? "translateY(0)" : "translateY(-4px)",
                  transition: "all 0.4s ease",
                  height: isActive ? "auto" : 0,
                  overflow: "hidden",
                }}
              >
                {step.description}
              </p>

              {/* Step number badge */}
              <div
                style={{
                  position: "absolute",
                  top: -4,
                  right: "calc(50% - 28px)",
                  width: 16,
                  height: 16,
                  borderRadius: "50%",
                  background: isDone ? step.color : isActive ? step.color : "#e8ecf1",
                  color: isDone || isActive ? "#fff" : "#94a3b8",
                  fontSize: 8,
                  fontWeight: 700,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  transition: "all 0.4s ease",
                  zIndex: 2,
                }}
              >
                {isDone ? "✓" : step.id}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
