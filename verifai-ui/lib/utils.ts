import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const VERDICT_STYLES = {
  PASS: {
    bg: "bg-emerald-500/15",
    text: "text-emerald-400",
    border: "border-emerald-500/30",
    dot: "bg-emerald-400",
  },
  SOFT_FLAG: {
    bg: "bg-amber-500/15",
    text: "text-amber-400",
    border: "border-amber-500/30",
    dot: "bg-amber-400",
  },
  BLOCK: {
    bg: "bg-red-500/15",
    text: "text-red-400",
    border: "border-red-500/30",
    dot: "bg-red-400",
  },
  PENDING: {
    bg: "bg-slate-500/15",
    text: "text-slate-400",
    border: "border-slate-500/30",
    dot: "bg-slate-400",
  },
} as const;

export const TIER_STYLES = {
  P: { label: "Primary", bg: "bg-blue-500/15", text: "text-blue-400" },
  A: { label: "Acceptable", bg: "bg-violet-500/15", text: "text-violet-400" },
  C: { label: "Conditional", bg: "bg-slate-500/15", text: "text-slate-400" },
  "?": { label: "Unclassified", bg: "bg-slate-500/15", text: "text-slate-400" },
} as const;

export function formatScore(score: number) {
  return `${Math.round(score * 100)}%`;
}

export function getVerdict(score: number): "PASS" | "SOFT_FLAG" | "BLOCK" {
  if (score >= 0.7) return "PASS";
  if (score >= 0.4) return "SOFT_FLAG";
  return "BLOCK";
}

export const CT_IDS = [
  "CT-101", "CT-107", "CT-201", "CT-301", "CT-311", "CT-401", "CT-501",
  "CT-601", "CT-606", "CT-701", "CT-702", "CT-705", "CT-801",
  "CT-803", "CT-901", "CT-909",
];
