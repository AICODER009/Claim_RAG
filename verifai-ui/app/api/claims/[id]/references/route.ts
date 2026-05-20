import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function POST(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const { refId, passageText, pageRef, tier, addedBy, note } = await req.json();
  if (!refId || !passageText || !addedBy) {
    return NextResponse.json({ error: "refId, passageText, addedBy required" }, { status: 400 });
  }

  const ref = await prisma.customReference.create({
    data: { claimId: params.id, refId, passageText, pageRef, tier, addedBy, note },
  });

  await prisma.claim.update({ where: { id: params.id }, data: { updatedAt: new Date() } });

  return NextResponse.json({ ok: true, id: ref.id });
}
