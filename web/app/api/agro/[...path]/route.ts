import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

async function proxy(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const workerUrl = process.env.WORKER_URL;
  const workerKey = process.env.WORKER_API_KEY;
  if (!workerUrl || !workerKey) return NextResponse.json({ error: "Worker agro non configuré" }, { status: 503 });
  const { path } = await context.params;
  // Tolère un éventuel préfixe client erroné `/agro/agro/*`.
  const normalizedPath = path[0] === "agro" ? path.slice(1) : path;
  const target = `${workerUrl.replace(/\/$/, "")}/agro/${normalizedPath.join("/")}${new URL(request.url).search}`;
  const headers = new Headers(request.headers);
  headers.set("X-API-Key", workerKey);
  headers.delete("host");
  const response = await fetch(target, { method: request.method, headers, body: ["GET", "HEAD"].includes(request.method) ? undefined : await request.arrayBuffer(), cache: "no-store" });
  const body = await response.arrayBuffer();
  return new NextResponse(body, { status: response.status, headers: { "Content-Type": response.headers.get("content-type") ?? "application/json" } });
}

export function GET(request: Request, context: { params: Promise<{ path: string[] }> }) { return proxy(request, context); }
export function POST(request: Request, context: { params: Promise<{ path: string[] }> }) { return proxy(request, context); }
export function PUT(request: Request, context: { params: Promise<{ path: string[] }> }) { return proxy(request, context); }
export function PATCH(request: Request, context: { params: Promise<{ path: string[] }> }) { return proxy(request, context); }
