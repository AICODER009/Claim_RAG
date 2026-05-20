"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

function timeAgo(date: string | Date): string {
  const seconds = Math.floor((Date.now() - new Date(date).getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

type Override = {
  id: string; previousVerdict: string; newVerdict: string;
  reason: string; overriddenBy: string; overriddenAt: Date;
};
type CustomRef = {
  id: string; refId: string; passageText: string;
  pageRef: string | null; tier: string; addedBy: string;
  addedAt: Date; note: string | null;
};

const VERDICT_OPTIONS = [
  { value: "PASS", label: "✓ Pass", color: "#10b981" },
  { value: "SOFT_FLAG", label: "⚠ Soft Flag", color: "#f59e0b" },
  { value: "BLOCK", label: "✕ Block", color: "#ef4444" },
];

const VERDICT_COLORS: Record<string, { bg: string; color: string; dot: string }> = {
  PASS: { bg: "rgba(16,185,129,0.1)", color: "#10b981", dot: "#34d399" },
  SOFT_FLAG: { bg: "rgba(245,158,11,0.1)", color: "#f59e0b", dot: "#fbbf24" },
  BLOCK: { bg: "rgba(239,68,68,0.1)", color: "#ef4444", dot: "#f87171" },
};

const labelStyle: React.CSSProperties = {
  fontSize: 10, fontWeight: 600, color: "var(--text-muted)",
  textTransform: "uppercase", letterSpacing: "0.08em",
  marginBottom: 6, display: "block",
};

const inputStyle: React.CSSProperties = {
  width: "100%", padding: "8px 12px", borderRadius: 8,
  border: "1px solid var(--border-subtle)", background: "var(--bg-tertiary)",
  color: "var(--text-primary)", fontSize: 12, fontFamily: "var(--font-sans)",
  outline: "none", transition: "border-color 0.2s",
};

export function OverridePanel({
  claim,
  overrides,
  customRefs,
}: {
  claim: { id: string };
  overrides: Override[];
  customRefs: CustomRef[];
}) {
  const router = useRouter();
  const [verdict, setVerdict] = useState("");
  const [reason, setReason] = useState("");
  const [reviewer, setReviewer] = useState("");
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [showRefForm, setShowRefForm] = useState(false);
  const [ref, setRef] = useState({ refId: "", passageText: "", pageRef: "", tier: "P", addedBy: "", note: "" });
  const [savingRef, setSavingRef] = useState(false);

  async function submitOverride(e: React.FormEvent) {
    e.preventDefault();
    if (!verdict || !reason || !reviewer) return;
    setSaving(true);
    setError("");
    try {
      const res = await fetch(`/api/claims/${claim.id}/override`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ newVerdict: verdict, reason: note ? `${reason}\n\nNote: ${note}` : reason, overriddenBy: reviewer }),
      });
      if (!res.ok) {
        const d = await res.json();
        setError(d.error ?? "Override failed");
      } else {
        setVerdict(""); setReason(""); setReviewer(""); setNote("");
        router.refresh();
      }
    } catch {
      setError("Network error — please try again");
    } finally {
      setSaving(false);
    }
  }

  async function submitRef(e: React.FormEvent) {
    e.preventDefault();
    if (!ref.refId || !ref.passageText || !ref.addedBy) return;
    setSavingRef(true);
    await fetch(`/api/claims/${claim.id}/references`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(ref),
    });
    setSavingRef(false);
    setRef({ refId: "", passageText: "", pageRef: "", tier: "P", addedBy: "", note: "" });
    setShowRefForm(false);
    router.refresh();
  }

  return (
    <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 24 }}>

      {/* ─── Override Verdict ─── */}
      <div>
        <h2 style={{
          fontSize: 11, fontWeight: 700, color: "var(--text-muted)",
          textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 16,
          display: "flex", alignItems: "center", gap: 6,
        }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
          </svg>
          Override Verdict
        </h2>

        <form onSubmit={submitOverride} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {/* Verdict Selection */}
          <div>
            <label style={labelStyle}>New Verdict</label>
            <div style={{ display: "flex", gap: 6 }}>
              {VERDICT_OPTIONS.map((v) => (
                <button
                  key={v.value}
                  type="button"
                  onClick={() => setVerdict(v.value)}
                  style={{
                    flex: 1, padding: "8px 4px", borderRadius: 8,
                    border: verdict === v.value ? `2px solid ${v.color}` : "1px solid var(--border-subtle)",
                    background: verdict === v.value ? `${v.color}15` : "var(--bg-tertiary)",
                    color: verdict === v.value ? v.color : "var(--text-secondary)",
                    fontSize: 11, fontWeight: 600, cursor: "pointer",
                    transition: "all 0.2s", textAlign: "center",
                  }}
                >
                  {v.label}
                </button>
              ))}
            </div>
          </div>

          {/* Reason */}
          <div>
            <label style={labelStyle}>Reason *</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              placeholder="Justification for override…"
              style={{ ...inputStyle, resize: "none", lineHeight: 1.6 }}
              required
            />
          </div>

          {/* Reviewer */}
          <div>
            <label style={labelStyle}>Reviewer Name *</label>
            <input
              value={reviewer}
              onChange={(e) => setReviewer(e.target.value)}
              placeholder="Your name"
              style={inputStyle}
              required
            />
          </div>

          {/* Optional note */}
          <div>
            <label style={labelStyle}>Score Note <span style={{ fontWeight: 400, opacity: 0.6 }}>(optional)</span></label>
            <input
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="e.g. Confirmed with Medical Affairs on 2026-05-19"
              style={inputStyle}
            />
          </div>

          {error && (
            <p style={{ fontSize: 11, color: "#f87171", padding: "6px 10px", borderRadius: 6, background: "rgba(239,68,68,0.08)" }}>
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={saving || !verdict || !reason || !reviewer}
            className="btn-accent"
            style={{ width: "100%", fontSize: 12, padding: "10px 0", opacity: saving || !verdict || !reason || !reviewer ? 0.5 : 1, cursor: saving || !verdict || !reason || !reviewer ? "not-allowed" : "pointer" }}
          >
            {saving ? "Saving…" : "Save Override"}
          </button>
        </form>
      </div>

      {/* ─── Override History ─── */}
      {overrides.length > 0 && (
        <div>
          <h2 style={{
            fontSize: 11, fontWeight: 700, color: "var(--text-muted)",
            textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 12,
            display: "flex", alignItems: "center", gap: 6,
          }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
            History ({overrides.length})
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {overrides.map((o, idx) => {
              const prev = VERDICT_COLORS[o.previousVerdict] ?? VERDICT_COLORS.BLOCK;
              const next = VERDICT_COLORS[o.newVerdict] ?? VERDICT_COLORS.BLOCK;
              const version = overrides.length - idx + 1;
              return (
                <div key={o.id} style={{ padding: 12, borderRadius: 10, background: "var(--bg-tertiary)", border: "1px solid var(--border-subtle)" }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <span style={{ fontSize: 9, fontWeight: 700, padding: "2px 8px", borderRadius: 99, background: prev.bg, color: prev.color }}>
                        {o.previousVerdict.replace("_", " ")}
                      </span>
                      <span style={{ fontSize: 11, color: "var(--text-muted)" }}>→</span>
                      <span style={{ fontSize: 9, fontWeight: 700, padding: "2px 8px", borderRadius: 99, background: next.bg, color: next.color }}>
                        {o.newVerdict.replace("_", " ")}
                      </span>
                    </div>
                    <span style={{ fontSize: 9, fontWeight: 700, color: "#818cf8", fontFamily: "var(--font-mono)" }}>v{version}</span>
                  </div>
                  <p style={{ fontSize: 11, color: "var(--text-secondary)", lineHeight: 1.5 }}>
                    {o.reason}
                  </p>
                  <p style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 4 }}>
                    {o.overriddenBy} · {timeAgo(o.overriddenAt)}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ─── Add Reference ─── */}
      <div>
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          marginBottom: 12,
        }}>
          <h2 style={{
            fontSize: 11, fontWeight: 700, color: "var(--text-muted)",
            textTransform: "uppercase", letterSpacing: "0.08em",
            display: "flex", alignItems: "center", gap: 6,
          }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M12 5v14M5 12h14" />
            </svg>
            Custom References
          </h2>
          <button
            onClick={() => setShowRefForm(!showRefForm)}
            style={{
              fontSize: 10, fontWeight: 600,
              color: showRefForm ? "var(--text-muted)" : "var(--accent-coral)",
              background: "transparent", border: "none", cursor: "pointer",
            }}
          >
            {showRefForm ? "Cancel" : "+ Add"}
          </button>
        </div>

        {showRefForm && (
          <form onSubmit={submitRef} style={{
            display: "flex", flexDirection: "column", gap: 10,
            padding: 14, borderRadius: 10,
            background: "var(--bg-tertiary)", border: "1px solid var(--border-subtle)",
            marginBottom: 12,
          }}>
            {/* Two-column row */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <div>
                <label style={labelStyle}>Ref ID *</label>
                <input
                  value={ref.refId}
                  onChange={(e) => setRef({ ...ref, refId: e.target.value })}
                  placeholder="Allen_Lancet_2024"
                  style={{ ...inputStyle, fontSize: 11 }}
                  required
                />
              </div>
              <div>
                <label style={labelStyle}>Page / Section</label>
                <input
                  value={ref.pageRef}
                  onChange={(e) => setRef({ ...ref, pageRef: e.target.value })}
                  placeholder="p.43, Table 3"
                  style={{ ...inputStyle, fontSize: 11 }}
                />
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <div>
                <label style={labelStyle}>Added By *</label>
                <input
                  value={ref.addedBy}
                  onChange={(e) => setRef({ ...ref, addedBy: e.target.value })}
                  placeholder="Your name"
                  style={{ ...inputStyle, fontSize: 11 }}
                  required
                />
              </div>
              <div>
                <label style={labelStyle}>Tier</label>
                <select
                  value={ref.tier}
                  onChange={(e) => setRef({ ...ref, tier: e.target.value })}
                  style={{ ...inputStyle, fontSize: 11 }}
                >
                  <option value="P">P – Primary</option>
                  <option value="A">A – Acceptable</option>
                  <option value="C">C – Conditional</option>
                </select>
              </div>
            </div>

            <div>
              <label style={labelStyle}>Passage Text *</label>
              <textarea
                value={ref.passageText}
                onChange={(e) => setRef({ ...ref, passageText: e.target.value })}
                rows={3}
                placeholder="Verbatim text from the source…"
                style={{ ...inputStyle, resize: "none", fontSize: 11, lineHeight: 1.6 }}
                required
              />
            </div>

            <div>
              <label style={labelStyle}>Note</label>
              <input
                value={ref.note}
                onChange={(e) => setRef({ ...ref, note: e.target.value })}
                placeholder="Reviewer comment…"
                style={{ ...inputStyle, fontSize: 11 }}
              />
            </div>

            <button
              type="submit"
              disabled={savingRef}
              className="btn-accent"
              style={{
                width: "100%", fontSize: 11, padding: "8px 0",
                opacity: savingRef ? 0.5 : 1,
              }}
            >
              {savingRef ? "Saving…" : "Add Reference"}
            </button>
          </form>
        )}

        {/* Existing custom refs */}
        {customRefs.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {customRefs.map((r) => (
              <div key={r.id} style={{
                padding: 10, borderRadius: 8,
                background: "var(--bg-tertiary)", border: "1px solid var(--border-subtle)",
                borderLeft: "3px solid #818cf8",
              }}>
                <p style={{ fontSize: 11, fontWeight: 600, color: "#818cf8", marginBottom: 3 }}>
                  {r.refId}
                </p>
                <p style={{
                  fontSize: 10, color: "var(--text-secondary)", lineHeight: 1.4,
                  overflow: "hidden", display: "-webkit-box",
                  WebkitLineClamp: 2, WebkitBoxOrient: "vertical",
                }}>
                  {r.passageText}
                </p>
                <p style={{ fontSize: 9, color: "var(--text-muted)", marginTop: 4 }}>
                  {r.addedBy} · {r.pageRef ?? "—"} · {timeAgo(r.addedAt)}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
