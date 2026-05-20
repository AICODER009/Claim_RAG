import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const { newVerdict, reason, overriddenBy } = await req.json();
  if (!newVerdict || !reason || !overriddenBy) {
    return NextResponse.json({ error: "Missing fields" }, { status: 400 });
  }

  const claim = await prisma.claim.findUnique({
    where: { id },
    include: { result: true, overrides: { orderBy: { overriddenAt: "desc" }, take: 1 } },
  });
  if (!claim) return NextResponse.json({ error: "Not found" }, { status: 404 });

  const previousVerdict =
    claim.overrides[0]?.newVerdict ?? claim.result?.verdict ?? "PENDING";

  await prisma.manualOverride.create({
    data: {
      claimId: id,
      previousVerdict,
      newVerdict,
      reason,
      overriddenBy,
    },
  });

  await prisma.claim.update({ where: { id }, data: { updatedAt: new Date() } });

  return NextResponse.json({ ok: true });
}
