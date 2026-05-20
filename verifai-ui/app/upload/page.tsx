"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import Link from "next/link";

type ClaimStatus = "queued" | "rewriting" | "retrieving" | "judging" | "done" | "error";

interface QueuedClaim {
  id: string;
  text: string;
  ctId: string;
  source: string;
  status: ClaimStatus;
  dbId?: number;
  verdict?: string;
  score?: number;
  error?: string;
}

const STORAGE_KEY = "verifai_queue_v1";

function loadQueue(): QueuedClaim[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed: QueuedClaim[] = JSON.parse(raw);
    // Any claim that was mid-flight when we left → reset to queued so user can retry
    return parsed.map((c) =>
      ["rewriting", "retrieving", "judging"].includes(c.status)
        ? { ...c, status: "queued" as const, error: "Interrupted — ready to retry" }
        : c
    );
  } catch {
    return [];
  }
}

function saveQueue(queue: QueuedClaim[]) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(queue)); } catch {}
}

const CT_IDS = [
  "CT-101", "CT-107", "CT-201", "CT-301", "CT-311", "CT-401", "CT-501",
  "CT-601", "CT-606", "CT-701", "CT-702", "CT-705", "CT-801",
  "CT-803", "CT-901", "CT-909",
];

const STATUS_STYLE: Record<string, { bg: string; color: string; label: string }> = {
  queued: { bg: "var(--bg-tertiary)", color: "var(--text-muted)", label: "Queued" },
  rewriting: { bg: "#eef2ff", color: "#6366f1", label: "Rewriting…" },
  retrieving: { bg: "#fff5f5", color: "#FF5F6D", label: "Retrieving…" },
  judging: { bg: "#fffbeb", color: "#f59e0b", label: "Judging…" },
  done: { bg: "#ecfdf5", color: "#059669", label: "Done" },
  error: { bg: "#fef2f2", color: "#dc2626", label: "Error" },
};

const VERDICT_STYLE: Record<string, { bg: string; color: string }> = {
  PASS: { bg: "#ecfdf5", color: "#059669" },
  SOFT_FLAG: { bg: "#fffbeb", color: "#d97706" },
  BLOCK: { bg: "#fef2f2", color: "#dc2626" },
};

function OrbitLoader({ size = 40 }: { size?: number }) {
  return (
    <div style={{ position: "relative", width: size, height: size }}>
      <div style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%,-50%)", width: size * 0.28, height: size * 0.28, borderRadius: "50%", background: "linear-gradient(135deg, #FF5F6D, #FF8A65)", opacity: 0.3 }} />
      {[0, 1, 2].map((i) => (
        <div key={i} style={{
          position: "absolute", top: "50%", left: "50%", width: 6, height: 6, marginLeft: -3, marginTop: -3,
          borderRadius: "50%", background: i % 2 === 0 ? "#FF5F6D" : "#FF8A65",
          animation: `orbit ${1.8 + i * 0.3}s linear infinite`, animationDelay: `${i * 0.4}s`, opacity: 1 - i * 0.2,
        }} />
      ))}
    </div>
  );
}

export default function SubstantiatePage() {
  const [claimText, setClaimText] = useState("");
  const [ctId, setCtId] = useState("CT-301");
  const [source, setSource] = useState("");
  const [queue, setQueue] = useState<QueuedClaim[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const processingRef = useRef(false);

  // Restore queue from localStorage on first render
  useEffect(() => {
    setQueue(loadQueue());
  }, []);

  // Persist queue to localStorage on every change
  useEffect(() => {
    if (queue.length > 0) saveQueue(queue);
  }, [queue]);

  // Add a single claim to queue (auto-detects bulk)
  function addToQueue() {
    if (!claimText.trim()) return;
    const lines = claimText.split("\n").map((l) => l.trim()).filter(Boolean);
    // If user has multiple lines, auto-route to bulk mode
    if (lines.length > 1) {
      addBulk();
      return;
    }
    const newClaim: QueuedClaim = {
      id: `q-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      text: claimText.trim(),
      ctId,
      source,
      status: "queued",
    };
    setQueue((prev) => [...prev, newClaim]);
    setClaimText("");
  }

  // Add multiple claims (one per line)
  function addBulk() {
    const lines = claimText.split("\n").map((l) => l.trim()).filter(Boolean);
    if (lines.length === 0) return;
    const newClaims: QueuedClaim[] = lines.map((line, i) => {
      // Support format: "CT-301 | claim text" for per-line CT-ID
      const pipeIdx = line.indexOf("|");
      let lineCtId = ctId;
      let text = line;
      if (pipeIdx > 0) {
        const prefix = line.slice(0, pipeIdx).trim().toUpperCase();
        if (/^CT-[A-Z0-9]+$/.test(prefix)) {
          lineCtId = prefix;
          text = line.slice(pipeIdx + 1).trim();
        }
      }
      return {
        id: `q-${Date.now()}-${i}-${Math.random().toString(36).slice(2, 6)}`,
        text,
        ctId: lineCtId,
        source,
        status: "queued" as const,
      };
    });
    setQueue((prev) => [...prev, ...newClaims]);
    setClaimText("");
  }

  function removeFromQueue(id: string) {
    setQueue((prev) => {
      const next = prev.filter((c) => c.id !== id);
      saveQueue(next);
      return next;
    });
  }

  function clearCompleted() {
    setQueue((prev) => {
      const next = prev.filter((c) => c.status !== "done");
      saveQueue(next);
      return next;
    });
  }

  // Update a specific claim's state
  const updateClaim = useCallback((id: string, updates: Partial<QueuedClaim>) => {
    setQueue((prev) => prev.map((c) => c.id === id ? { ...c, ...updates } : c));
  }, []);

  // Process a single claim through the pipeline
  async function processSingleClaim(claim: QueuedClaim) {
    try {
      // Step 1: Create claim in DB
      updateClaim(claim.id, { status: "rewriting" });
      const claimRes = await fetch("/api/claims", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: claim.text, ctId: claim.ctId, source: claim.source }),
      });
      if (!claimRes.ok) throw new Error("Failed to create claim");
      const { id: dbId } = await claimRes.json();
      updateClaim(claim.id, { dbId });

      // Step 2: Substantiate
      updateClaim(claim.id, { status: "retrieving" });
      const subRes = await fetch("/api/substantiate", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ claimId: dbId, claimText: claim.text, ctId: claim.ctId }),
      });

      updateClaim(claim.id, { status: "judging" });
      if (!subRes.ok) throw new Error(await subRes.text());
      const result = await subRes.json();

      updateClaim(claim.id, {
        status: "done",
        verdict: result.verdict ?? "PASS",
        score: result.coverageScore ?? 0,
      });
    } catch (err) {
      updateClaim(claim.id, { status: "error", error: String(err) });
    }
  }

  // Process all queued claims sequentially
  async function processQueue() {
    if (processingRef.current) return;
    processingRef.current = true;
    setIsProcessing(true);

    // Get current queue snapshot
    const currentQueue = [...queue];
    for (const claim of currentQueue) {
      if (claim.status !== "queued") continue;
      await processSingleClaim(claim);
    }

    processingRef.current = false;
    setIsProcessing(false);
  }

  const queuedCount = queue.filter((c) => c.status === "queued").length;
  const doneCount = queue.filter((c) => c.status === "done").length;
  const errorCount = queue.filter((c) => c.status === "error").length;
  const activeItem = queue.find((c) => ["rewriting", "retrieving", "judging"].includes(c.status));

  return (
    <div style={{ padding: "28px 36px", height: "100%", display: "flex", flexDirection: "column", boxSizing: "border-box" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.02em", marginBottom: 4 }}>
            Substantiate Claims
          </h1>
          <p style={{ fontSize: 14, color: "var(--text-muted)" }}>
            Add claims to queue, then process them sequentially against the evidence corpus
          </p>
        </div>
        {queue.length > 0 && (
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <span style={{ fontSize: 12, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
              {doneCount}/{queue.length} done
            </span>
            {queuedCount > 0 && (
              <button onClick={processQueue} disabled={isProcessing} className="btn-accent"
                style={{ fontSize: 13, display: "flex", alignItems: "center", gap: 8 }}>
                {isProcessing ? (
                  <><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: "dna-rotate 1s linear infinite" }}><path d="M21 12a9 9 0 11-6.219-8.56"/></svg>Processing…</>
                ) : (
                  <>Run Queue ({queuedCount})<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg></>
                )}
              </button>
            )}
          </div>
        )}
      </div>

      {/* Input area — flex:1 so it fills remaining vertical space */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 380px", gap: 20, alignItems: "stretch", flex: 1, minHeight: 0 }}>

        {/* Left: Claim Input */}
        <div className="glass-card-static" style={{ padding: 24, display: "flex", flexDirection: "column", minHeight: 0 }}>
          <h2 style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 14 }}>
            Add Claims
          </h2>

          <div style={{ marginBottom: 14, flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
            <textarea value={claimText} onChange={(e) => setClaimText(e.target.value)}
              placeholder={"Enter claims to substantiate…\n\nSingle: Just type the claim text\nBulk (1 per line): Use CT-ID | claim format:\nCT-301 | VYVGART Hytrulo had a demonstrated safety profile in ADHERE\nCT-201 | The efficacy and safety of VYVGART Hytrulo were demonstrated in CIDP\nCT-601 | The recommended dose is 1,008 mg efgartigimod alfa SC QW"}
              className="input-field" style={{ resize: "none", fontFamily: "var(--font-sans)", lineHeight: 1.6, fontSize: 13, flex: 1 }} />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
            <div>
              <label style={{ display: "block", fontSize: 10, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 5 }}>
                Claim Type (CT-ID)
              </label>
              <select value={ctId} onChange={(e) => setCtId(e.target.value)} className="input-field" style={{ cursor: "pointer" }}>
                {CT_IDS.map((id) => (<option key={id} value={id}>{id}</option>))}
              </select>
            </div>
            <div>
              <label style={{ display: "block", fontSize: 10, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 5 }}>
                Source / Campaign
              </label>
              <input value={source} onChange={(e) => setSource(e.target.value)} placeholder="e.g. Q2 Campaign Brief" className="input-field" />
            </div>
          </div>

          <div style={{ display: "flex", gap: 10 }}>
            <button type="button" onClick={addToQueue} disabled={!claimText.trim()}
              style={{
                flex: 1, padding: "10px 16px", borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: "pointer",
                border: "1px solid var(--accent-coral)", background: "transparent", color: "var(--accent-coral)",
                opacity: claimText.trim() ? 1 : 0.4, transition: "all 0.2s",
              }}>
              + Add Single Claim
            </button>
            <button type="button" onClick={addBulk} disabled={!claimText.trim()}
              className="btn-accent" style={{ flex: 1, fontSize: 13, display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              Add Bulk (1 per line)
            </button>
          </div>
        </div>

        {/* Right: Queue Status — stretches to full height of left panel */}
        <div className="glass-card-static" style={{ padding: 24, display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
            <h2 style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
              Queue ({queue.length})
            </h2>
            {queue.length > 0 && (
              <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 99, background: "#ecfdf5", color: "#059669", fontWeight: 600 }}>{doneCount} ✓</span>
                {errorCount > 0 && <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 99, background: "#fef2f2", color: "#dc2626", fontWeight: 600 }}>{errorCount} ✗</span>}
                <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 99, background: "var(--bg-tertiary)", color: "var(--text-muted)", fontWeight: 600 }}>{queuedCount} pending</span>
                {doneCount > 0 && (
                  <button onClick={clearCompleted} style={{ fontSize: 9, padding: "2px 8px", borderRadius: 6, border: "1px solid var(--border-subtle)", background: "transparent", color: "var(--text-muted)", cursor: "pointer" }}>
                    Clear Done
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Currently processing */}
          {activeItem && (
            <div style={{
              padding: 14, borderRadius: 10, marginBottom: 12,
              background: STATUS_STYLE[activeItem.status].bg,
              border: `1px solid ${STATUS_STYLE[activeItem.status].color}30`,
              display: "flex", alignItems: "center", gap: 12,
            }}>
              <OrbitLoader size={32} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ fontSize: 11, fontWeight: 600, color: STATUS_STYLE[activeItem.status].color }}>
                  {STATUS_STYLE[activeItem.status].label}
                </p>
                <p style={{ fontSize: 11, color: "var(--text-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {activeItem.text.slice(0, 60)}…
                </p>
              </div>
            </div>
          )}

          {/* Queue list */}
          <div style={{ display: "flex", flexDirection: "column", gap: 4, flex: 1, overflowY: "auto", minHeight: 0 }}>
            {queue.length === 0 ? (
              <div style={{ padding: "40px 16px", textAlign: "center" }}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="1.5" style={{ margin: "0 auto 10px", opacity: 0.4 }}>
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                </svg>
                <p style={{ fontSize: 12, color: "var(--text-muted)" }}>No claims in queue</p>
                <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4, opacity: 0.6 }}>Add claims from the left panel</p>
              </div>
            ) : queue.map((claim) => {
              const s = STATUS_STYLE[claim.status];
              const vs = claim.verdict ? VERDICT_STYLE[claim.verdict] : null;
              return (
                <div key={claim.id}>
                  <div style={{
                    display: "flex", alignItems: "center", gap: 10, padding: "8px 10px",
                    borderRadius: claim.status === "error" && claim.error ? "8px 8px 0 0" : 8,
                    border: "1px solid var(--border-subtle)",
                    borderBottom: claim.status === "error" && claim.error ? "none" : "1px solid var(--border-subtle)",
                    background: claim.status === "done" ? "#ecfdf505" : "transparent",
                    transition: "all 0.3s",
                  }}>
                    {/* Status dot */}
                    <div style={{
                      width: 8, height: 8, borderRadius: "50%", flexShrink: 0,
                      background: s.color,
                      animation: ["rewriting", "retrieving", "judging"].includes(claim.status) ? "pulse-ring 1.5s ease infinite" : "none",
                    }} />

                    {/* Claim text */}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p style={{ fontSize: 11, color: "var(--text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {claim.text.slice(0, 50)}{claim.text.length > 50 ? "…" : ""}
                      </p>
                      <div style={{ display: "flex", gap: 6, marginTop: 3, flexWrap: "wrap" }}>
                        <span style={{ fontSize: 9, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>{claim.ctId}</span>
                        <span style={{ fontSize: 9, padding: "0 5px", borderRadius: 99, background: s.bg, color: s.color, fontWeight: 600 }}>
                          {s.label}
                        </span>
                        {vs && claim.verdict && (
                          <span style={{ fontSize: 9, padding: "0 5px", borderRadius: 99, background: vs.bg, color: vs.color, fontWeight: 600 }}>
                            {claim.verdict.replace("_", " ")} {claim.score ? `${Math.round(claim.score * 100)}%` : ""}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    {claim.status === "queued" && (
                      <button onClick={() => removeFromQueue(claim.id)} style={{
                        width: 22, height: 22, borderRadius: 6, border: "1px solid var(--border-subtle)",
                        background: "transparent", color: "var(--text-muted)", cursor: "pointer", fontSize: 12,
                        display: "flex", alignItems: "center", justifyContent: "center",
                      }}>×</button>
                    )}
                    {claim.status === "done" && claim.dbId && (
                      <Link href={`/claims/${claim.dbId}`} style={{
                        fontSize: 10, color: "var(--accent-coral)", textDecoration: "none", fontWeight: 600,
                      }}>View →</Link>
                    )}
                    {claim.status === "error" && (
                      <button onClick={() => { updateClaim(claim.id, { status: "queued", error: undefined }); }} style={{
                        fontSize: 9, padding: "2px 8px", borderRadius: 6,
                        border: "1px solid #fecaca", background: "#fef2f2", color: "#dc2626",
                        cursor: "pointer", fontWeight: 600,
                      }}>Retry</button>
                    )}
                  </div>
                  {/* Error detail below the row */}
                  {claim.status === "error" && claim.error && (
                    <div style={{
                      padding: "6px 10px", marginBottom: 4,
                      borderRadius: "0 0 8px 8px", fontSize: 10, lineHeight: 1.5,
                      background: "#fef2f2", border: "1px solid #fecaca", borderTop: "none",
                      color: "#dc2626", wordBreak: "break-word",
                    }}>
                      <strong>Error:</strong> {claim.error.length > 200 ? claim.error.slice(0, 200) + "…" : claim.error}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Run button at bottom */}
          {queuedCount > 0 && !isProcessing && (
            <button onClick={processQueue} className="btn-accent"
              style={{ width: "100%", marginTop: 14, fontSize: 13, display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
              Process {queuedCount} Claim{queuedCount > 1 ? "s" : ""} Sequentially
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </button>
          )}
        </div>
      </div>

      {/* Info footer */}
      <div className="glass-card-static" style={{ marginTop: 16, padding: "14px 18px", display: "flex", gap: 10, alignItems: "flex-start" }}>
        <img src="/logo.png" alt="" style={{ height: 18, marginTop: 2 }} />
        <p style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.7 }}>
          <strong style={{ color: "var(--text-primary)" }}>Queue Mode:</strong> Claims are processed one at a time to avoid rate-limiting. Each claim goes through: Query Rewrite → 3-Signal Retrieval → LLM Judge → Verdict. Add as many claims as needed — they&apos;ll be processed sequentially.
        </p>
      </div>
    </div>
  );
}
