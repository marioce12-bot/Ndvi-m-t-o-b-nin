import { NextResponse } from "next/server";
import { getAdminDb } from "@/lib/firebase-admin";

export const dynamic = "force-dynamic";

export async function GET(_request: Request, context: { params: Promise<{ jobId: string }> }) {
  try {
    const { jobId } = await context.params;
    const snapshot = await getAdminDb().collection("jobs").doc(jobId).get();
    if (!snapshot.exists) return NextResponse.json({ error: "Job introuvable" }, { status: 404 });
    return NextResponse.json({ id: snapshot.id, ...snapshot.data() });
  } catch (error) {
    console.error("Job route error", error);
    return NextResponse.json({ error: "Firestore indisponible" }, { status: 503 });
  }
}
