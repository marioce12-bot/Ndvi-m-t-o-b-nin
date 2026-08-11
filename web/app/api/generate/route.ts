import { NextResponse } from "next/server";
import { getAdminDb } from "@/lib/firebase-admin";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const payload = await request.json();
    const { jobId, pentadeId, product, email, force = false } = payload;
    if (!jobId || !pentadeId || !email || !["ndvi", "anomaly"].includes(product)) {
      return NextResponse.json({ error: "Paramètres invalides" }, { status: 400 });
    }
    const workerUrl = process.env.WORKER_URL;
    const workerKey = process.env.WORKER_API_KEY;
    if (!workerUrl || !workerKey) return NextResponse.json({ error: "Worker non configure" }, { status: 503 });
    const db = getAdminDb();
    await db.collection("jobs").doc(jobId).set({ product, pentadeId, email, status: "pending", imageUrl: null, thumbnailUrl: null, error: null, createdAt: new Date(), startedAt: null, completedAt: null }, { merge: true });
    const response = await fetch(`${workerUrl.replace(/\/$/, "")}/generate`, { method: "POST", headers: { "X-API-Key": workerKey, "Content-Type": "application/json" }, body: JSON.stringify({ jobId, pentadeId, product, email, force }) });
    const body = await response.json();
    if (!response.ok) return NextResponse.json(body, { status: response.status });
    return NextResponse.json({ jobId, ...body }, { status: response.status });
  } catch (error) {
    console.error("Generate route error", error);
    return NextResponse.json({ error: "Impossible de lancer la génération" }, { status: 500 });
  }
}
