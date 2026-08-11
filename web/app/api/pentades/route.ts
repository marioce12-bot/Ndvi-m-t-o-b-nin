import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const product = new URL(request.url).searchParams.get("product") ?? "anomaly";
  const workerUrl = process.env.WORKER_URL;
  const workerKey = process.env.WORKER_API_KEY;
  if (!workerUrl || !workerKey) return NextResponse.json({ error: "Worker non configure" }, { status: 503 });
  const response = await fetch(`${workerUrl.replace(/\/$/, "")}/pentades?product=${encodeURIComponent(product)}`, {
    headers: { "X-API-Key": workerKey }, cache: "no-store",
  });
  const body = await response.json();
  return NextResponse.json(body, { status: response.status });
}
