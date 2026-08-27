import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

async function workerRequest(request: Request, method: string) {
  const workerUrl = process.env.WORKER_URL;
  const workerKey = process.env.WORKER_API_KEY;
  if (!workerUrl || !workerKey) return NextResponse.json({ error: "Worker agro non configuré" }, { status: 503 });
  const target = `${workerUrl.replace(/\/$/, "")}/agro/stations${new URL(request.url).search}`;
  const response = await fetch(target, { method, headers: { "X-API-Key": workerKey }, cache: "no-store" });
  const raw = await response.text();
  let body: unknown;
  try { body = raw ? JSON.parse(raw) : { error: `Réponse worker vide (${response.status})` }; }
  catch { body = { error: `Réponse worker invalide (${response.status})` }; }
  return NextResponse.json(body, { status: response.status });
}

export function GET(request: Request) { return workerRequest(request, "GET"); }

export async function POST(request: Request) {
  const workerUrl = process.env.WORKER_URL;
  const workerKey = process.env.WORKER_API_KEY;
  if (!workerUrl || !workerKey) return NextResponse.json({ error: "Worker agro non configuré" }, { status: 503 });
  const response = await fetch(`${workerUrl.replace(/\/$/, "")}/agro/stations`, { method: "POST", headers: { "X-API-Key": workerKey, "Content-Type": "application/json" }, body: await request.text() });
  const raw = await response.text();
  let body: unknown;
  try { body = raw ? JSON.parse(raw) : { error: `Réponse worker vide (${response.status})` }; }
  catch { body = { error: `Réponse worker invalide (${response.status})` }; }
  return NextResponse.json(body, { status: response.status });
}
