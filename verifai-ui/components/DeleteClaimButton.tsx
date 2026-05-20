"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function DeleteClaimButton({ claimId }: { claimId: string }) {
  const router = useRouter();
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function handleDelete() {
    setDeleting(true);
    try {
      const res = await fetch("/api/claims", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: claimId }),
      });
      if (res.ok) {
        router.push("/claims");
        router.refresh();
      }
    } catch {
      setDeleting(false);
    }
  }

  if (!confirming) {
    return (
      <button
        onClick={() => setConfirming(true)}
        style={{
          display: "inline-flex", alignItems: "center", gap: 5,
          padding: "6px 14px", borderRadius: 8,
          border: "1px solid var(--border-subtle)",
          background: "transparent", color: "var(--text-muted)",
          fontSize: 11, cursor: "pointer", transition: "all 0.2s",
        }}
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="3 6 5 6 21 6" />
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
        </svg>
        Delete
      </button>
    );
  }

  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
      <span style={{ fontSize: 11, color: "#ef4444" }}>Delete?</span>
      <button
        onClick={handleDelete}
        disabled={deleting}
        style={{
          padding: "4px 12px", borderRadius: 6,
          border: "1px solid #fecaca", background: "#fef2f2",
          color: "#dc2626", fontSize: 10, fontWeight: 600,
          cursor: "pointer", opacity: deleting ? 0.5 : 1,
        }}
      >
        {deleting ? "..." : "Yes"}
      </button>
      <button
        onClick={() => setConfirming(false)}
        style={{
          padding: "4px 12px", borderRadius: 6,
          border: "1px solid var(--border-subtle)", background: "transparent",
          color: "var(--text-muted)", fontSize: 10, cursor: "pointer",
        }}
      >
        No
      </button>
    </div>
  );
}
