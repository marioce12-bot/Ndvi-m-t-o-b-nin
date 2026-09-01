import { NextResponse } from "next/server";
import { getSupabaseAdmin, verifyRequestUser } from "@/lib/supabase-admin";

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
    if (typeof pentadeId !== "string" || !["ndvi", "anomaly"].includes(product)) {
      return NextResponse.json({ error: "Paramètres invalides" }, { status: 400 });
    }
    const workerUrl = process.env.WORKER_URL;
    const workerKey = process.env.WORKER_API_KEY;
    if (!workerUrl || !workerKey) return NextResponse.json({ error: "Worker non configure" }, { status: 503 });
    const jobEmail = email ?? "platform@local";
    const { error: insertError } = await getSupabaseAdmin().from("jobs").upsert({ id: jobId, owner_id: user.id === "platform" ? null : user.id, product, pentade_id: pentadeId, email: jobEmail, status: "pending", image_url: null, thumbnail_url: null, error: null, started_at: null, completed_at: null });
    if (insertError) throw insertError;
    console.info("Platform generation job created", { jobId, pentadeId, product });
    const workerOwnerId = user.id === "platform" ? null : user.id;
    const response = await fetch(`${workerUrl.replace(/\/$/, "")}/generate`, { method: "POST", headers: { "X-API-Key": workerKey, "Content-Type": "application/json" }, body: JSON.stringify({ jobId, pentadeId, product, email: jobEmail, ownerId: workerOwnerId, force }) });
    const rawBody = await response.text();
    let body: unknown;
    try { body = JSON.parse(rawBody); } catch { body = { error: rawBody || "Réponse worker invalide" }; }
    console.info("Worker generation response", { jobId, status: response.status, body });
    if (!response.ok) return NextResponse.json({ error: "Worker generation rejected request", workerStatus: response.status, worker: body, sent: { jobId, pentadeId, product, ownerId: user.id } }, { status: response.status });
    return NextResponse.json({ jobId, ...(body && typeof body === "object" ? body : {}) }, { status: response.status });
  } catch (error) {
    console.error("Generate route error", error);
    console.error("Generate route error", error);
    return NextResponse.json({ error: error instanceof Error && error.message === "AUTH_REQUIRED" ? "Authentification requise" : error instanceof Error ? error.message : "Impossible de lancer la génération" }, { status: error instanceof Error && error.message === "AUTH_REQUIRED" ? 401 : 500 });
  }
}
