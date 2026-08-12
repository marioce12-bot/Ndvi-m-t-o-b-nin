import { NextResponse } from "next/server";
import { getAdminDb, verifyRequestUser } from "@/lib/firebase-admin";

export const dynamic = "force-dynamic";

export async function GET(_request: Request, context: { params: Promise<{ jobId: string }> }) {
  try {
    const { jobId } = await context.params;
    const user = await verifyRequestUser(_request);
    const snapshot = await getAdminDb().collection("jobs").doc(jobId).get();
    if (!snapshot.exists) return NextResponse.json({ error: "Job introuvable" }, { status: 404 });
    const data = snapshot.data();
    if (data?.ownerId !== user.uid) return NextResponse.json({ error: "Accès interdit" }, { status: 403 });
    return NextResponse.json({ id: snapshot.id, ...data });
  } catch (error) {
    console.error("Job route error", error);
    return NextResponse.json({ error: error instanceof Error && error.message === "AUTH_REQUIRED" ? "Authentification requise" : "Firestore indisponible" }, { status: error instanceof Error && error.message === "AUTH_REQUIRED" ? 401 : 503 });
  }
}
