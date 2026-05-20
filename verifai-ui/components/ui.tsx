"use client";

import { cn, VERDICT_STYLES } from "@/lib/utils";

type Verdict = "PASS" | "SOFT_FLAG" | "BLOCK" | "PENDING";

export function VerdictBadge({ verdict }: { verdict: string }) {
  const style = VERDICT_STYLES[verdict as Verdict] ?? VERDICT_STYLES.PENDING;
  const labels: Record<string, string> = {
    PASS: "PASS",
    SOFT_FLAG: "SOFT FLAG",
    BLOCK: "BLOCK",
    PENDING: "PENDING",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border tracking-wide",
        style.bg, style.text, style.border
      )}
    >
      <span className={cn("w-1.5 h-1.5 rounded-full", style.dot)} />
      {labels[verdict] ?? verdict}
    </span>
  );
}

export function TierBadge({ tier }: { tier: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    P: { label: "Primary", cls: "bg-blue-500/15 text-blue-400 border-blue-500/30" },
    A: { label: "Acceptable", cls: "bg-violet-500/15 text-violet-400 border-violet-500/30" },
    C: { label: "Conditional", cls: "bg-slate-500/15 text-slate-400 border-slate-500/30" },
  };
  const t = map[tier] ?? { label: tier || "?", cls: "bg-slate-500/15 text-slate-400 border-slate-500/30" };
  return (
    <span className={cn("inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold border", t.cls)}>
      {t.label}
    </span>
  );
}

export function ScoreBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    score >= 0.7 ? "bg-emerald-400" : score >= 0.4 ? "bg-amber-400" : "bg-red-400";
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-500", color)}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-mono text-slate-400 w-8 text-right">{pct}%</span>
    </div>
  );
}

export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between px-8 pt-8 pb-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-100">{title}</h1>
        {subtitle && <p className="text-sm text-slate-400 mt-1">{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}
