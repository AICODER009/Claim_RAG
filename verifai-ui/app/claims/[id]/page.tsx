import { prisma } from "@/lib/prisma";
import { notFound } from "next/navigation";
import { OverridePanel } from "@/components/OverridePanel";
import { DeleteClaimButton } from "@/components/DeleteClaimButton";
import Link from "next/link";

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

export const dynamic = "force-dynamic";

function VerdictBadgeInline({ verdict }: { verdict: string }) {
  const map: Record<string, { bg: string; color: string; dot: string; label: string }> = {
    PASS: { bg: "rgba(16,185,129,0.12)", color: "#34d399", dot: "#10b981", label: "PASS" },
    SOFT_FLAG: { bg: "rgba(245,158,11,0.12)", color: "#fbbf24", dot: "#f59e0b", label: "SOFT FLAG" },
    BLOCK: { bg: "rgba(239,68,68,0.12)", color: "#f87171", dot: "#ef4444", label: "BLOCK" },
    PENDING: { bg: "rgba(100,116,139,0.12)", color: "#94a3b8", dot: "#64748b", label: "PENDING" },
  };
  const v = map[verdict] ?? map.PENDING;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 6,
      padding: "5px 14px", borderRadius: 99,
      fontSize: 11, fontWeight: 700, letterSpacing: "0.06em",
      background: v.bg, color: v.color,
      border: `1px solid ${v.color}30`,
      boxShadow: `0 0 16px ${v.color}18`,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: v.dot }} />
      {v.label}
    </span>
  );
}

function TierBadgeInline({ tier }: { tier: string }) {
  const map: Record<string, { label: string; color: string; bg: string }> = {
    P: { label: "Primary", color: "#818cf8", bg: "rgba(99,102,241,0.12)" },
    A: { label: "Acceptable", color: "#a78bfa", bg: "rgba(139,92,246,0.12)" },
    C: { label: "Conditional", color: "#94a3b8", bg: "rgba(100,116,139,0.12)" },
  };
  const t = map[tier] ?? { label: tier || "?", color: "#94a3b8", bg: "rgba(100,116,139,0.12)" };
  return (
    <span style={{
      display: "inline-flex", alignItems: "center",
      padding: "2px 8px", borderRadius: 6,
      fontSize: 9, fontWeight: 700,
      background: t.bg, color: t.color,
    }}>
      {t.label}
    </span>
  );
}

export default async function ClaimDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const claim = await prisma.claim.findUnique({
    where: { id },
    include: {
      result: true,
      overrides: { orderBy: { overriddenAt: "desc" } },
      customRefs: { orderBy: { addedAt: "desc" } },
    },
  });

  if (!claim) notFound();

  // Serialize through JSON to strip Prisma wrapper types (Decimal, Date → plain values)
  const safe = JSON.parse(JSON.stringify(claim));
  const result = safe.result;
  const activeVerdict = safe.overrides[0]?.newVerdict ?? result?.verdict ?? "PENDING";

  const subAssertions = result?.subAssertions ? JSON.parse(result.subAssertions) : [];
  const passages: Array<{
    ref_id: string; rt_id?: string; tier?: string; section?: string;
    segment_type?: string; text: string; numeric_tokens?: string[]; score?: number;
  }> = result?.passages ? JSON.parse(result.passages) : [];

  const customPassages = safe.customRefs.map((r: any) => ({
    ref_id: r.refId, tier: r.tier, text: r.passageText,
    section: r.pageRef ?? undefined,
    _custom: true, _note: r.note, _addedBy: r.addedBy,
  }));

  const allPassages = [...passages, ...customPassages];

  // Key Reference: extract "Passage N" from judge assessment text (1-indexed → 0-indexed)
  // e.g. "...substantiated by Passage 1, RT-101..." → keyRefIndex = 0
  const assessmentText: string = String(result?.assessment ?? "");
  const keyRefIndex = (() => {
    const match = assessmentText.match(/[Pp]assage\s+(\d+)/);
    if (match) {
      const n = parseInt(match[1], 10) - 1;
      if (n >= 0 && n < passages.length) return n;
    }
    // Fallback: highest retrieval score
    let maxScore = -1, maxIdx = -1;
    passages.forEach((p, i) => { const s = Number(p.score ?? 0); if (s > maxScore) { maxScore = s; maxIdx = i; } });
    return maxIdx;
  })();

  const rawScore = result ? Number(result.coverageScore) : 0;
  const scorePct = rawScore > 1 ? Math.round(rawScore) : Math.round(rawScore * 100);
  const scoreColor = scorePct >= 80 ? "#10b981" : scorePct >= 60 ? "#f59e0b" : "#ef4444";

  return (
    <div style={{ padding: "28px 36px" }}>
      {/* Top bar */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
        <Link href="/claims" style={{
          display: "inline-flex", alignItems: "center", gap: 4,
          fontSize: 12, color: "var(--text-muted)", textDecoration: "none",
          transition: "color 0.2s",
        }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M15 18l-6-6 6-6"/>
          </svg>
          Back to Claims
        </Link>
        <DeleteClaimButton claimId={safe.id} />
      </div>

      {/* Claim Header Card */}
      <div className="glass-card-static" style={{ padding: 24, marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 24 }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ fontSize: 12, fontFamily: "var(--font-mono)", color: "#818cf8", marginBottom: 8, fontWeight: 600 }}>
              {String(safe.ctId ?? "")}
            </p>
            <h1 style={{ fontSize: 16, fontWeight: 600, color: "var(--text-primary)", lineHeight: 1.6, letterSpacing: "-0.01em", wordBreak: "break-word" }}>
              {String(safe.text ?? "")}
            </h1>
            {safe.source && (
              <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 6 }}>
                Source: {String(safe.source)}
              </p>
            )}
            {result && (
              <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 8 }}>
                Run {timeAgo(result.runAt)} · {String(result.modelJudge ?? "")}
                {result.rewrittenQuery && (
                  <> · Query: <em style={{ color: "var(--text-secondary) " }}>&quot;{String(result.rewrittenQuery)}&quot;</em></>
                )}
              </p>
            )}
          </div>

          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 10, flexShrink: 0 }}>
            <VerdictBadgeInline verdict={activeVerdict} />
            {result && (
              <div style={{ width: 160, display: "flex", alignItems: "center", gap: 8 }}>
                <div style={{ flex: 1, height: 5, background: "var(--border-subtle)", borderRadius: 99, overflow: "hidden" }}>
                  <div style={{
                    height: "100%", borderRadius: 99, width: `${scorePct}%`,
                    background: `linear-gradient(90deg, ${scoreColor}, ${scoreColor}88)`,
                    transition: "width 1s ease",
                  }} />
                </div>
                <span style={{ fontSize: 12, fontFamily: "var(--font-mono)", color: scoreColor, fontWeight: 600 }}>
                  {scorePct}%
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 3-column grid body */}
      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr 300px", gap: 16 }}>

        {/* LEFT: Sub-assertions */}
        <div className="glass-card-static" style={{ padding: 20 }}>
          <h2 style={{
            fontSize: 10, fontWeight: 700, color: "var(--text-muted)",
            textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 14,
          }}>
            Sub-Assertions ({subAssertions.length})
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {subAssertions.map((sa: {
              sub_assertion: string; is_covered: boolean;
              evidence_text?: string; source_passage?: string;
            }, i: number) => (
              <div key={i} style={{
                padding: 12, borderRadius: 10,
                background: "var(--bg-tertiary)",
                border: "1px solid var(--border-subtle)",
                borderLeft: `3px solid ${sa.is_covered ? "#10b981" : "#ef4444"}`,
              }}>
                <div style={{ display: "flex", alignItems: "flex-start", gap: 8 }}>
                  {sa.is_covered ? (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#34d399" strokeWidth="2.5" style={{ flexShrink: 0, marginTop: 1 }}>
                      <circle cx="12" cy="12" r="10" strokeWidth="1.5" />
                      <path d="M9 12l2 2 4-4"/>
                    </svg>
                  ) : (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#f87171" strokeWidth="2.5" style={{ flexShrink: 0, marginTop: 1 }}>
                      <circle cx="12" cy="12" r="10" strokeWidth="1.5" />
                      <path d="M15 9l-6 6M9 9l6 6"/>
                    </svg>
                  )}
                  <p style={{ fontSize: 12, color: "var(--text-primary)", lineHeight: 1.5 }}>
                    {typeof sa.sub_assertion === "object" ? JSON.stringify(sa.sub_assertion) : String(sa.sub_assertion || "")}
                  </p>
                </div>
                {sa.evidence_text && (
                  <p style={{
                    fontSize: 10, fontFamily: "var(--font-mono)",
                    color: "var(--text-muted)", marginTop: 8, fontStyle: "italic",
                    lineHeight: 1.5, overflow: "hidden",
                    display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical",
                  }}>
                    &ldquo;{typeof sa.evidence_text === "object" ? JSON.stringify(sa.evidence_text) : String(sa.evidence_text || "")}&rdquo;
                  </p>
                )}
              </div>
            ))}
            {subAssertions.length === 0 && (
              <p style={{ fontSize: 12, color: "var(--text-muted)", textAlign: "center", padding: "40px 0" }}>
                No sub-assertions available
              </p>
            )}
          </div>

          {result?.assessment && (
            <div style={{ marginTop: 20, padding: 14, borderRadius: 10, background: "var(--bg-tertiary)", border: "1px solid var(--border-subtle)" }}>
              <h2 style={{
                fontSize: 10, fontWeight: 700, color: "var(--text-muted)",
                textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 10,
              }}>
                Judge Assessment
              </h2>
              <p style={{
                fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.7,
                wordBreak: "break-word", whiteSpace: "pre-wrap", overflowWrap: "anywhere",
              }}>
                {typeof result.assessment === "object" ? JSON.stringify(result.assessment, null, 2) : String(result.assessment || "")}
              </p>
            </div>
          )}
        </div>

        {/* CENTER: Evidence Passages */}
        <div className="glass-card-static" style={{ padding: 20 }}>
          <div style={{
            display: "flex", alignItems: "center", justifyContent: "space-between",
            marginBottom: 10,
          }}>
            <h2 style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.1em" }}>
              Evidence Passages ({allPassages.length})
            </h2>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="1.5">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
            </svg>
          </div>

          {/* How passages work — explanation */}
          <div style={{ marginBottom: 12, padding: "8px 12px", borderRadius: 8, background: "rgba(99,102,241,0.06)", border: "1px solid rgba(99,102,241,0.12)" }}>
            <p style={{ fontSize: 11, color: "var(--text-secondary)", lineHeight: 1.6 }}>
              <strong style={{ color: "var(--text-primary)" }}>How this works:</strong>{" "}
              The pipeline retrieved {allPassages.filter(p => !("_custom" in p)).length} candidate passages from your reference documents.
              The AI judge read all of them together and determined which one(s) directly support each sub-assertion.
              The <strong style={{ color: "#10b981" }}>highest-scored passage</strong> is the primary reference — the others provided supporting context.
            </p>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {allPassages.map((p, i) => {
              const isCustom = "_custom" in p && p._custom;
              const isKeyRef = !isCustom && i === keyRefIndex;
              return (
                <div key={i} style={{
                  padding: 16, borderRadius: 12,
                  background: isKeyRef ? "rgba(16,185,129,0.04)" : "var(--bg-tertiary)",
                  border: isKeyRef ? "1.5px solid rgba(16,185,129,0.35)" : "1px solid var(--border-subtle)",
                  borderLeft: isCustom ? "3px solid #6366f1" : isKeyRef ? "3px solid #10b981" : undefined,
                }}>
                  {/* Header */}
                  <div style={{
                    display: "flex", alignItems: "center", justifyContent: "space-between",
                    gap: 12, marginBottom: 8, flexWrap: "wrap",
                  }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--text-muted)", background: "var(--bg-tertiary)", padding: "2px 6px", borderRadius: 4, border: "1px solid var(--border-subtle)" }}>
                        #{i + 1}
                      </span>
                      {isKeyRef && (
                        <span style={{ fontSize: 8, fontWeight: 700, padding: "2px 8px", borderRadius: 99, background: "rgba(16,185,129,0.15)", color: "#10b981", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                          ★ Key Reference
                        </span>
                      )}
                      <span style={{ fontSize: 11, fontWeight: 700, fontFamily: "var(--font-mono)", color: isKeyRef ? "#10b981" : "#818cf8", maxWidth: 240, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {String(p.ref_id ?? "")}
                      </span>
                      {isCustom && (
                        <span style={{ fontSize: 8, fontWeight: 700, background: "rgba(99,102,241,0.15)", color: "#818cf8", padding: "2px 6px", borderRadius: 4, textTransform: "uppercase", letterSpacing: "0.1em" }}>
                          User Added
                        </span>
                      )}
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      {(p as any).tier && <TierBadgeInline tier={(p as any).tier} />}
                      {(p as any).segment_type && (
                        <span style={{ fontSize: 9, color: "var(--text-muted)", textTransform: "uppercase" }}>
                          {String((p as any).segment_type)}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Reference document — always shown */}
                  {(() => {
                    const refTitle = String((p as any).ref_title || "").trim();
                    const docTitle = String((p as any).doc_title || "").trim();
                    const refId = String(p.ref_id || "");
                    const fallbackTitle = refId.replace(/[-_]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
                    // Priority: ref_title (GPT-extracted from PDF) → doc_title → formatted ref_id
                    const displayTitle = refTitle || docTitle || fallbackTitle;
                    const isReal = !!(refTitle || docTitle);
                    const author = String((p as any).doc_author || "").trim();
                    const year = String((p as any).doc_year || "").trim();
                    const journal = String((p as any).doc_journal || "").trim();
                    const doi = String((p as any).doc_doi || "").trim();
                    const page = (p as any).page;
                    const meta = [author, year, journal].filter(Boolean).join(" · ");
                    return (
                      <div style={{ marginBottom: 8, padding: "7px 10px", borderRadius: 6, background: "rgba(129,140,248,0.07)", border: "1px solid rgba(129,140,248,0.18)" }}>
                        <div style={{ display: "flex", alignItems: "flex-start", gap: 8 }}>
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#818cf8" strokeWidth="1.8" style={{ flexShrink: 0, marginTop: 2 }}>
                            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
                          </svg>
                          <div style={{ flex: 1 }}>
                            <p style={{ fontSize: 11, fontWeight: 600, color: "var(--text-primary)", lineHeight: 1.4 }}>
                              {displayTitle}
                              {!isReal && <span style={{ fontSize: 9, color: "var(--text-muted)", fontWeight: 400, marginLeft: 6 }}>(ref ID)</span>}
                            </p>
                            {meta && <p style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>{meta}</p>}
                            {doi && <p style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "#818cf8", marginTop: 2, opacity: 0.7 }}>DOI: {doi}</p>}
                          </div>
                          {page != null && (
                            <span style={{ fontSize: 9, fontFamily: "var(--font-mono)", background: "rgba(129,140,248,0.12)", color: "#818cf8", padding: "2px 7px", borderRadius: 4, flexShrink: 0, fontWeight: 600 }}>
                              p.{page}
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })()}

                  {/* Meta */}
                  <div style={{ display: "flex", gap: 12, marginBottom: 8, fontSize: 10, color: "var(--text-muted)", flexWrap: "wrap" }}>
                    {(p as any).section && <span>§ {String((p as any).section)}</span>}
                    {"rt_id" in p && p.rt_id && <span>RT: {String(p.rt_id)}</span>}
                    {"score" in p && p.score != null && (
                      <span>Score: {typeof p.score === "number" ? p.score.toFixed(3) : String(p.score)}</span>
                    )}
                  </div>

                  {/* Text */}
                  <p style={{ fontFamily: "var(--font-mono)", fontSize: 12, lineHeight: 1.7, color: "var(--text-secondary)", wordBreak: "break-word", whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>
                    {String(p.text ?? "")}
                  </p>

                  {/* Numeric tokens */}
                  {"numeric_tokens" in p && Array.isArray(p.numeric_tokens) && p.numeric_tokens.length > 0 && (() => {
                    // Extract plain string from {value, context} objects (old DB format)
                    const flatTokens = p.numeric_tokens
                      .map((t: unknown) =>
                        t && typeof t === "object"
                          ? String((t as any).value ?? (t as any).context ?? "")
                          : String(t ?? "")
                      )
                      .filter(Boolean)
                      .slice(0, 12);
                    if (flatTokens.length === 0) return null;
                    return (
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 8 }}>
                        <span style={{ fontSize: 9, color: "var(--text-muted)", alignSelf: "center" }}>Nums:</span>
                        {flatTokens.map((tok: string, j: number) => (
                          <span key={j} style={{ fontSize: 9, fontFamily: "var(--font-mono)", background: "rgba(255,142,83,0.08)", color: "#ffb088", padding: "2px 6px", borderRadius: 4 }}>
                            {tok}
                          </span>
                        ))}
                      </div>
                    );
                  })()}

                  {"_note" in p && p._note && (
                    <p style={{ fontSize: 10, color: "#818cf8", marginTop: 8, fontStyle: "italic" }}>
                      Note: {String(p._note)}
                    </p>
                  )}
                </div>
              );
            })}
            {allPassages.length === 0 && (
              <p style={{ fontSize: 12, color: "var(--text-muted)", textAlign: "center", padding: "60px 0" }}>
                No evidence passages retrieved
              </p>
            )}
          </div>
        </div>

        {/* RIGHT: Override Panel */}
        <div className="glass-card-static" style={{ padding: 0 }}>
          <OverridePanel
            claim={safe}
            overrides={safe.overrides}
            customRefs={safe.customRefs}
          />
        </div>
      </div>
    </div>
  );
}
