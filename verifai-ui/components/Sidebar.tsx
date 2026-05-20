"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import { useTheme } from "./ThemeProvider";

const nav = [
  {
    href: "/",
    label: "Dashboard",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" rx="1.5" />
        <rect x="14" y="3" width="7" height="7" rx="1.5" />
        <rect x="3" y="14" width="7" height="7" rx="1.5" />
        <rect x="14" y="14" width="7" height="7" rx="1.5" />
      </svg>
    ),
  },
  {
    href: "/claims",
    label: "Claims",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
      </svg>
    ),
  },
  {
    href: "/upload",
    label: "Substantiate",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <path d="M9 12l2 2 4-4" />
      </svg>
    ),
  },
  {
    href: "/report",
    label: "Report",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <path d="M8 13h2M8 17h2M12 13h4M12 17h4" />
      </svg>
    ),
  },
  {
    href: "/howitworks",
    label: "How It Works",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
      </svg>
    ),
  },
  {
    href: "/settings",
    label: "Settings",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="3" />
        <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
      </svg>
    ),
  },
];

export function Sidebar() {
  const path = usePathname();
  const { theme, toggle } = useTheme();
  const [collapsed, setCollapsed] = useState(false);

  // Persist collapse state across navigation
  useEffect(() => {
    const stored = localStorage.getItem("sidebar-collapsed");
    if (stored === "true") setCollapsed(true);
  }, []);

  function toggleCollapsed() {
    setCollapsed((prev) => {
      localStorage.setItem("sidebar-collapsed", String(!prev));
      return !prev;
    });
  }

  const W = collapsed ? 56 : 230;

  return (
    <aside
      style={{
        width: W,
        flexShrink: 0,
        display: "flex",
        flexDirection: "column",
        borderRight: "1px solid var(--border-subtle)",
        background: "var(--sidebar-bg)",
        transition: "width 0.22s cubic-bezier(0.4,0,0.2,1)",
        overflow: "hidden",
        position: "relative",
      }}
    >
      {/* Logo + collapse toggle */}
      <div style={{
        padding: collapsed ? "18px 0" : "18px 16px",
        borderBottom: "1px solid var(--border-subtle)",
        display: "flex", alignItems: "center",
        justifyContent: collapsed ? "center" : "space-between",
        gap: 8,
        transition: "padding 0.22s",
      }}>
        {!collapsed && (
          <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
            <img src="/logo.png" alt="Revisto" style={{ height: 28, objectFit: "contain", objectPosition: "left" }} />
            <span style={{ fontSize: 9, fontWeight: 600, letterSpacing: "0.12em", textTransform: "uppercase" }}>
              <span style={{
                background: "linear-gradient(90deg, #FF5F6D, #FF8A65)",
                WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
              }}>Evidence-backed. </span>
              <span style={{ color: "var(--text-primary)", WebkitTextFillColor: "var(--text-primary)" }}>Always</span>
            </span>
          </div>
        )}
        {collapsed && (
          <img src="/logo-icon.png" alt="Revisto" style={{ height: 26, objectFit: "contain" }}
            onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
        )}

        {/* Collapse toggle button */}
        <button
          onClick={toggleCollapsed}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          style={{
            width: 26, height: 26, borderRadius: 6, flexShrink: 0,
            border: "1px solid var(--border-subtle)",
            background: "var(--bg-tertiary)",
            color: "var(--text-muted)",
            cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
            transition: "all 0.2s",
          }}
          onMouseEnter={(e) => { e.currentTarget.style.color = "var(--accent-coral)"; e.currentTarget.style.borderColor = "var(--accent-coral)"; }}
          onMouseLeave={(e) => { e.currentTarget.style.color = "var(--text-muted)"; e.currentTarget.style.borderColor = "var(--border-subtle)"; }}
        >
          {/* Chevron flips when collapsed */}
          <svg
            width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
            style={{ transform: collapsed ? "rotate(180deg)" : "none", transition: "transform 0.22s" }}
          >
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: collapsed ? "12px 6px" : "12px 10px", transition: "padding 0.22s" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {nav.map(({ href, icon, label }) => {
            const active = href === "/" ? path === "/" : path.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                title={collapsed ? label : undefined}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: collapsed ? 0 : 10,
                  padding: collapsed ? "9px 0" : "9px 12px",
                  justifyContent: collapsed ? "center" : "flex-start",
                  borderRadius: 8,
                  fontSize: 13,
                  fontWeight: active ? 600 : 400,
                  color: active ? "var(--accent-coral)" : "var(--text-secondary)",
                  background: active
                    ? theme === "dark" ? "rgba(255,95,109,0.1)" : "#fff5f5"
                    : "transparent",
                  border: active
                    ? theme === "dark" ? "1px solid rgba(255,95,109,0.2)" : "1px solid #fecaca"
                    : "1px solid transparent",
                  textDecoration: "none",
                  transition: "all 0.2s ease",
                  overflow: "hidden",
                  whiteSpace: "nowrap",
                }}
              >
                <span style={{ flexShrink: 0 }}>{icon}</span>
                {/* Label fades out when collapsed */}
                <span style={{
                  opacity: collapsed ? 0 : 1,
                  maxWidth: collapsed ? 0 : 160,
                  transition: "opacity 0.15s, max-width 0.22s",
                  overflow: "hidden",
                }}>
                  {label}
                </span>
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Dark mode toggle */}
      <div style={{ padding: collapsed ? "12px 6px" : "12px 16px", borderTop: "1px solid var(--border-subtle)", transition: "padding 0.22s" }}>
        <button
          onClick={toggle}
          title={theme === "light" ? "Switch to Dark Mode" : "Switch to Light Mode"}
          style={{
            width: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: collapsed ? "center" : "flex-start",
            gap: 8,
            padding: collapsed ? "8px 0" : "8px 10px",
            borderRadius: 8,
            border: "1px solid var(--border-subtle)",
            background: "var(--bg-tertiary)",
            color: "var(--text-secondary)",
            fontSize: 12,
            cursor: "pointer",
            transition: "all 0.2s",
            overflow: "hidden",
            whiteSpace: "nowrap",
          }}
        >
          <span style={{ flexShrink: 0 }}>
            {theme === "light" ? (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
            ) : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
            )}
          </span>
          <span style={{ opacity: collapsed ? 0 : 1, maxWidth: collapsed ? 0 : 120, transition: "opacity 0.15s, max-width 0.22s", overflow: "hidden" }}>
            {theme === "light" ? "Dark Mode" : "Light Mode"}
          </span>
        </button>
      </div>

      {/* Footer */}
      {!collapsed && (
        <div style={{ padding: "10px 16px", borderTop: "1px solid var(--border-subtle)" }}>
          <p style={{ fontSize: 10, color: "var(--text-muted)", lineHeight: 1.5 }}>
            Claim Substantiation
            <br />
            Requirements v1.1
          </p>
        </div>
      )}
    </aside>
  );
}
