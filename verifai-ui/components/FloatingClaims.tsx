"use client";

import { useEffect, useState } from "react";

const CLAIMS = [
  { text: "Treatment efficacy substantiated by Reference 1, Page 20", verdict: "PASS" },
  { text: "Corresponding safety information not found", verdict: "BLOCK" },
  { text: "Punctuation: Insert comma before \"and\"", verdict: "SOFT_FLAG" },
  { text: "Proper use of Registered Trademark", verdict: "PASS" },
  { text: "54 claims generated from 35 references", verdict: "PASS" },
];

const VERDICT_CFG = {
  PASS: { bg: "#ecfdf5", border: "#a7f3d0", color: "#059669" },
  SOFT_FLAG: { bg: "#fffbeb", border: "#fde68a", color: "#d97706" },
  BLOCK: { bg: "#fef2f2", border: "#fecaca", color: "#dc2626" },
};

export function FloatingClaims() {
  const [visibleCount, setVisibleCount] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setVisibleCount((c) => {
        if (c < CLAIMS.length) return c + 1;
        setTimeout(() => setVisibleCount(0), 2000);
        return c;
      });
    }, 800);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="glass-card-static" style={{ padding: 20, position: "relative", overflow: "hidden", minHeight: 220 }}>
      <h2 style={{ fontSize: 11, fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 14 }}>
        Live Verification
      </h2>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {CLAIMS.slice(0, visibleCount).map((claim, i) => {
          const cfg = VERDICT_CFG[claim.verdict as keyof typeof VERDICT_CFG] ?? VERDICT_CFG.PASS;
          return (
            <div key={i} className="animate-float-up" style={{
              display: "flex", alignItems: "center", gap: 10, padding: "8px 12px",
              borderRadius: 8, background: cfg.bg, border: `1px solid ${cfg.border}`,
              animationDelay: `${i * 0.08}s`,
            }}>
              {claim.verdict === "PASS" ? (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={cfg.color} strokeWidth="2.5"><circle cx="12" cy="12" r="10" strokeWidth="1.5" fill={cfg.bg}/><path d="M9 12l2 2 4-4"/></svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><rect x="3" y="3" width="18" height="18" rx="3" fill={cfg.bg} stroke={cfg.color} strokeWidth="1.5"/></svg>
              )}
              <span style={{ fontSize: 11, color: "#475569", flex: 1 }}>{claim.text}</span>
              {claim.verdict === "PASS" ? (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="3"><path d="M5 12l5 5L19 7"/></svg>
              ) : (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={cfg.color} strokeWidth="3"><path d="M7 7l10 10M17 7l-10 10"/></svg>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
