import { NextResponse } from "next/server";
import { getAdminDb, verifyRequestUser } from "@/lib/firebase-admin";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(request: Request) {
  try {
    const user = await verifyRequestUser(request);
    const payload = await request.json();
    const jobId = typeof payload.jobId === "string" && payload.jobId ? payload.jobId : `job-${Date.now()}-${crypto.randomUUID().slice(0, 8)}`;
    const pentadeId = payload.pentade ?? payload.pentadeId;
    const force = payload.force === true;
    const email = user.email;
    const product = payload.product;
    if (typeof pentadeId !== "string" || !email || !["ndvi", "anomaly"].includes(product)) {
      return NextResponse.json({ error: "Paramètres invalides" }, { status: 400 });
    }
    const workerUrl = process.env.WORKER_URL;
    const workerKey = process.env.WORKER_API_KEY;
    if (!workerUrl || !workerKey) return NextResponse.json({ error: "Worker non configure" }, { status: 503 });
    const db = getAdminDb();
    await db.collection("jobs").doc(jobId).set({ ownerId: user.uid, product, pentadeId, email, status: "pending", imageUrl: null, thumbnailUrl: null, error: null, createdAt: new Date(), startedAt: null, completedAt: null }, { merge: true });
    const response = await fetch(`${workerUrl.replace(/\/$/, "")}/generate`, { method: "POST", headers: { "X-API-Key": workerKey, "Content-Type": "application/json" }, body: JSON.stringify({ jobId, pentadeId, product, email, ownerId: user.uid, force }) });
    const body = await response.json();
    if (!response.ok) return NextResponse.json(body, { status: response.status });
    return NextResponse.json({ jobId, ...body }, { status: response.status });
  } catch (error) {
    console.error("Generate route error", error);
    return NextResponse.json({ error: error instanceof Error && error.message === "AUTH_REQUIRED" ? "Authentification requise" : "Impossible de lancer la génération" }, { status: error instanceof Error && error.message === "AUTH_REQUIRED" ? 401 : 500 });
  }
}
