import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const verdict = searchParams.get("verdict");
  const q = searchParams.get("q");
  const page = parseInt(searchParams.get("page") ?? "1");
  const perPage = 50;

  const where: Record<string, unknown> = {};
  if (q) where.text = { contains: q };

  const [claims, total] = await Promise.all([
    prisma.claim.findMany({
      where,
      take: perPage,
      skip: (page - 1) * perPage,
      orderBy: { updatedAt: "desc" },
      include: {
        result: { select: { verdict: true, coverageScore: true, runAt: true } },
        overrides: { orderBy: { overriddenAt: "desc" }, take: 1 },
      },
    }),
    prisma.claim.count({ where }),
  ]);

  return NextResponse.json({ claims, total, page, perPage });
}

export async function POST(req: NextRequest) {
  const { text, ctId, source } = await req.json();
  if (!text || !ctId) {
    return NextResponse.json({ error: "text and ctId required" }, { status: 400 });
  }
  const claim = await prisma.claim.create({ data: { text, ctId, source } });
  return NextResponse.json({ id: claim.id });
}

export async function DELETE(req: NextRequest) {
  const { id } = await req.json();
  if (!id) {
    return NextResponse.json({ error: "id required" }, { status: 400 });
  }
  try {
    // Read claim before deletion for the audit log
    const claim = await prisma.claim.findUnique({
      where: { id },
      include: {
        result: { select: { verdict: true, coverageScore: true } },
        overrides: { orderBy: { overriddenAt: "desc" }, take: 1 },
      },
    });

    if (claim) {
      const norm = (v: unknown) => { const n = Number(v ?? 0); return n > 1 ? n / 100 : n; };
      const verdict = claim.overrides[0]?.newVerdict ?? claim.result?.verdict ?? "PENDING";
      const score = norm(claim.result?.coverageScore ?? 0);
      // Write audit record (best-effort — don't fail the delete if this errors)
      try {
        await (prisma as any).deletedClaim.create({
          data: {
            originalId: claim.id,
            text: claim.text,
            ctId: claim.ctId,
            source: claim.source ?? null,
            verdict,
            score,
          },
        });
      } catch {
        // Migration may not have run yet — ignore
      }
    }

    await prisma.claim.delete({ where: { id } });
    return NextResponse.json({ ok: true });
  } catch {
    return NextResponse.json({ error: "Claim not found" }, { status: 404 });
  }
}
