import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const workerUrl = process.env.WORKER_URL;
  const workerKey = process.env.WORKER_API_KEY;
  if (!workerUrl || !workerKey) return NextResponse.json({ error: "Worker agro non configuré" }, { status: 503 });
  const response = await fetch(`${workerUrl.replace(/\/$/, "")}/agro/stations${request.nextUrl.search}`, { headers: { "X-API-Key": workerKey }, cache: "no-store" });
  const body = await response.arrayBuffer();
  return new NextResponse(body, { status: response.status, headers: { "Content-Type": response.headers.get("content-type") ?? "application/json" } });
}

export async function POST(request: NextRequest) {
  const workerUrl = process.env.WORKER_URL;
  const workerKey = process.env.WORKER_API_KEY;
  if (!workerUrl || !workerKey) return NextResponse.json({ error: "Worker agro non configuré" }, { status: 503 });
  const response = await fetch(`${workerUrl.replace(/\/$/, "")}/agro/stations`, { method: "POST", headers: { "X-API-Key": workerKey, "Content-Type": "application/json" }, body: await request.arrayBuffer() });
  const body = await response.arrayBuffer();
  return new NextResponse(body, { status: response.status, headers: { "Content-Type": response.headers.get("content-type") ?? "application/json" } });
}
