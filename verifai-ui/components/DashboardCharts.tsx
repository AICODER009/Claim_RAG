"use client";

import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  AreaChart, Area, XAxis, YAxis, CartesianGrid, ReferenceLine, Legend,
} from "recharts";

const VERDICT_COLORS: Record<string, string> = {
  PASS: "#10b981",
  SOFT_FLAG: "#f59e0b",
  BLOCK: "#ef4444",
  PENDING: "#cbd5e1",
};

const VERDICT_LABELS: Record<string, string> = {
  PASS: "Substantiated",
  SOFT_FLAG: "Flagged",
  BLOCK: "Blocked",
  PENDING: "Pending",
};

export function DashboardCharts({
  verdictCounts,
  scores,
  claimLabels,
}: {
  verdictCounts: Record<string, number>;
  scores: number[];
  claimLabels?: string[];
}) {
  const pieData = Object.entries(verdictCounts)
    .filter(([, v]) => v > 0)
    .map(([name, value]) => ({ name, value }));

  const total = Object.values(verdictCounts).reduce((a, b) => a + b, 0);

  // Dual-series: Coverage Score vs MLR Threshold (70%)
  const areaData = scores.map((score, i) => ({
    claim: claimLabels?.[i] ?? `C${i + 1}`,
    coverage: score,
    threshold: 70,
  }));

  const avgCoverage = scores.length > 0
    ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
    : 0;

  const aboveThreshold = scores.filter(s => s >= 70).length;

  return (
    <>
      {/* Verdict Donut */}
      <div className="glass-card-static" style={{ padding: 20 }}>
        <h2 style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 14 }}>
          Verdict Distribution
        </h2>
        {pieData.length > 0 ? (
          <>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={80} paddingAngle={3} dataKey="value" strokeWidth={0}>
                  {pieData.map((entry) => (
                    <Cell key={entry.name} fill={VERDICT_COLORS[entry.name] ?? "#cbd5e1"} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)", borderRadius: 8, color: "var(--text-primary)", fontSize: 12, boxShadow: "0 4px 16px rgba(0,0,0,0.08)" }}
                  formatter={(value: number, name: string) => [value, VERDICT_LABELS[name] ?? name]}
                />
                <text x="50%" y="46%" textAnchor="middle" dominantBaseline="middle" style={{ fill: "var(--text-primary)", fontSize: 22, fontWeight: 700 }}>{total}</text>
                <text x="50%" y="58%" textAnchor="middle" dominantBaseline="middle" style={{ fill: "var(--text-muted)", fontSize: 9, fontWeight: 600, letterSpacing: "0.1em" }}>CLAIMS</text>
              </PieChart>
            </ResponsiveContainer>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginTop: 6, justifyContent: "center" }}>
              {Object.entries(VERDICT_COLORS).map(([label, color]) => (
                <div key={label} style={{ display: "flex", alignItems: "center", gap: 5 }}>
                  <div style={{ width: 8, height: 8, borderRadius: "50%", background: color }} />
                  <span style={{ fontSize: 10, color: "var(--text-muted)" }}>{VERDICT_LABELS[label] ?? label}</span>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div style={{ height: 200, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-muted)", fontSize: 13 }}>No data yet</div>
        )}
      </div>

      {/* Coverage Score vs MLR Threshold — Dual-series smooth area */}
      <div className="glass-card-static" style={{ padding: 20 }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 14 }}>
          <div>
            <h2 style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
              Coverage vs MLR Threshold
            </h2>
            <p style={{ fontSize: 10, color: "var(--text-secondary)", marginTop: 3 }}>
              Claims above 70% qualify for regulatory approval
            </p>
          </div>
          {scores.length > 0 && (
            <div style={{ textAlign: "right" }}>
              <p style={{ fontSize: 18, fontWeight: 700, color: aboveThreshold === scores.length ? "#10b981" : "#f59e0b" }}>
                {aboveThreshold}/{scores.length}
              </p>
              <p style={{ fontSize: 9, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>above threshold</p>
            </div>
          )}
        </div>

        {areaData.length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={areaData} margin={{ top: 5, right: 10, bottom: 0, left: -20 }}>
              <defs>
                {/* Coverage score — blue gradient */}
                <linearGradient id="gradCoverage" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#6366f1" stopOpacity={0.5} />
                  <stop offset="60%" stopColor="#818cf8" stopOpacity={0.15} />
                  <stop offset="100%" stopColor="#818cf8" stopOpacity={0.02} />
                </linearGradient>
                {/* Threshold — green gradient */}
                <linearGradient id="gradThreshold" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#10b981" stopOpacity={0.03} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" strokeOpacity={0.4} />
              <XAxis
                dataKey="claim"
                tick={{ fill: "var(--text-muted)", fontSize: 9 }}
                tickLine={false}
                axisLine={{ stroke: "var(--border-subtle)" }}
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fill: "var(--text-muted)", fontSize: 10 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) => `${v}%`}
              />
              <Tooltip
                contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)", borderRadius: 10, color: "var(--text-primary)", fontSize: 12, boxShadow: "0 8px 24px rgba(0,0,0,0.12)", padding: "8px 14px" }}
                labelStyle={{ color: "var(--text-muted)", fontSize: 10, marginBottom: 4, fontWeight: 600 }}
                formatter={(value: number, name: string) => [
                  `${value}%`,
                  name === "coverage" ? "Coverage Score" : "MLR Pass Threshold",
                ]}
              />
              <Legend
                wrapperStyle={{ fontSize: 10, paddingTop: 8 }}
                formatter={(value) => value === "coverage" ? "Coverage Score" : "MLR Pass Threshold (70%)"}
              />
              {/* Pass threshold reference line */}
              <ReferenceLine y={70} stroke="#10b981" strokeDasharray="4 3" strokeWidth={1} strokeOpacity={0.6} />
              {/* Threshold area (always at 70) */}
              <Area
                type="monotone"
                dataKey="threshold"
                stroke="#10b981"
                strokeWidth={2}
                strokeDasharray="5 3"
                fill="url(#gradThreshold)"
                dot={false}
                activeDot={false}
              />
              {/* Coverage score area */}
              <Area
                type="monotone"
                dataKey="coverage"
                stroke="#6366f1"
                strokeWidth={2.5}
                fill="url(#gradCoverage)"
                dot={{ r: 4, fill: "#6366f1", stroke: "#fff", strokeWidth: 2 }}
                activeDot={{ r: 6, fill: "#6366f1", stroke: "#fff", strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ height: 200, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 8, color: "var(--text-muted)", fontSize: 13 }}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2" opacity={0.4}>
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
            Substantiate claims to see coverage trend
          </div>
        )}
      </div>
    </>
  );
}

