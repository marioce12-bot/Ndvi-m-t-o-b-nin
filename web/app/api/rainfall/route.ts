import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

async function callWorker(url: string, init: RequestInit): Promise<Response> {
  let lastError: unknown;
  for (const [attempt, delay] of [ [1, 0], [2, 3000], [3, 8000] ] as const) {
    if (delay) await sleep(delay);
    try {
      const response = await fetch(url, { ...init, signal: AbortSignal.timeout(attempt === 1 ? 20000 : 10000) });
      if (response.ok || (response.status >= 400 && response.status < 500)) return response;
      lastError = new Error(`Worker HTTP ${response.status}`);
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError instanceof Error ? lastError : new Error("Worker inaccessible après 3 tentatives");
}

const tableDefinitions = [
  { id: "decades", title: "DECADES", description: "Entrée réseau pluviométrique : relevés journaliers par poste et par décade.", editable: true },
  { id: "agro", title: "RENSEIGNEMENTS AGRO", description: "Entrée stations synoptiques : observations météo par station et par jour.", editable: true },
  { id: "normales", title: "NORMALES", description: "Référentiels intégrés : normales pluviométriques RESA et normales agro-synoptiques.", editable: false },
  { id: "resa", title: "RESA-01", description: "Sortie automatisée calculée à partir des deux entrées et de l’historique.", editable: false },
] as const;

export async function GET(request: Request) {
  if (new URL(request.url).searchParams.get("output") === "xlsx") {
    const workerUrl = process.env.WORKER_URL; const workerKey = process.env.WORKER_API_KEY;
    if (!workerUrl || !workerKey) return NextResponse.json({ error: "Worker non configuré" }, { status: 503 });
    const response = await callWorker(`${workerUrl.replace(/\/$/, "")}/rainfall/output.xlsx`, { headers: { "X-API-Key": workerKey } });
    const buffer = await response.arrayBuffer();
    return new Response(buffer, { status: response.status, headers: { "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "Content-Disposition": "attachment; filename=RESA-01.xlsx" } });
  }
  return NextResponse.json({
    tableDefinitions,
    inputModel: {
      requiredFiles: ["DECADES_xxx.xlsx", "Renseignements_Agro_xxx.xls"],
      history: "Les relevés sont conservés par poste, année et code de décade; un nouvel upload ne remplace pas les décades précédentes.",
      defaultReference: "La feuille Normales est intégrée comme référentiel par défaut.",
    },
    seasons: {
      north: { start: "01-04", end: "31-10", areas: ["Atacora", "Donga", "Borgou", "Alibori"] },
      south: { seasons: [{ start: "01-03", end: "31-07" }, { start: "01-09", end: "30-11" }], areas: ["Collines", "Zou", "Mono", "Couffo", "Atlantique", "Littoral", "Ouémé", "Plateau"] },
    },
  });
}

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const source = formData.get("source");
    const file = formData.get("file");
    const workerUrl = process.env.WORKER_URL;
    const workerKey = process.env.WORKER_API_KEY;
    if (!(file instanceof File) || (source !== "decades" && source !== "agro")) return NextResponse.json({ error: "Fichier ou source invalide" }, { status: 400 });
    if (!workerUrl || !workerKey) return NextResponse.json({ error: "WORKER_URL et WORKER_API_KEY doivent être configurées dans Vercel" }, { status: 503 });
    const upstream = new FormData();
    upstream.set("file", file, file.name);
    const query = new URLSearchParams({ source: String(source) });
    for (const key of ["year", "month", "decade"]) { const value = formData.get(key); if (value) query.set(key, String(value)); }
    const response = await callWorker(`${workerUrl.replace(/\/$/, "")}/rainfall/import?${query.toString()}`, { method: "POST", headers: { "X-API-Key": workerKey }, body: upstream });
    const raw = await response.text();
    let body: Record<string, unknown>;
    try { body = raw.trim() ? JSON.parse(raw) : { error: `Worker vide (${response.status})` }; }
    catch { console.error("Rainfall worker invalid response", { status: response.status, body: raw.slice(0, 1000) }); body = { error: `Réponse worker invalide (${response.status})`, raw: raw.slice(0, 300) }; }
    return NextResponse.json(body, { status: response.ok ? 200 : response.status });
  } catch (error) {
    console.error("Rainfall API proxy error", error);
    return NextResponse.json({ error: error instanceof Error ? error.message : "Erreur interne pendant l’import" }, { status: 502 });
  }
}

export async function PUT() {
  const workerUrl = process.env.WORKER_URL;
  const workerKey = process.env.WORKER_API_KEY;
  if (!workerUrl || !workerKey) return NextResponse.json({ error: "Worker non configuré" }, { status: 503 });
  try {
    const response = await callWorker(`${workerUrl.replace(/\/$/, "")}/rainfall/imports`, { headers: { "X-API-Key": workerKey }, cache: "no-store" });
    const raw = await response.text();
    let body: Record<string, unknown>;
    try { body = raw.trim() ? JSON.parse(raw) : { error: `Worker vide (${response.status})` }; }
    catch { console.error("Rainfall imports invalid response", { status: response.status, body: raw.slice(0, 1000) }); body = { error: `Réponse worker invalide (${response.status})`, raw: raw.slice(0, 300) }; }
    return NextResponse.json(body, { status: response.ok ? 200 : response.status });
  } catch (error) {
    console.error("Rainfall imports proxy error", error);
    return NextResponse.json({ error: error instanceof Error ? error.message : "Worker inaccessible" }, { status: 502 });
  }
}

export async function PATCH(request: Request) {
  const workerUrl = process.env.WORKER_URL;
  const workerKey = process.env.WORKER_API_KEY;
  const jobId = new URL(request.url).searchParams.get("jobId");
  if (!workerUrl || !workerKey || !jobId) return NextResponse.json({ error: "Worker ou jobId manquant" }, { status: 400 });
  try {
    const response = await callWorker(`${workerUrl.replace(/\/$/, "")}/rainfall/import-jobs/${encodeURIComponent(jobId)}`, { headers: { "X-API-Key": workerKey }, cache: "no-store" });
    const raw = await response.text();
    let body: Record<string, unknown>;
    try { body = raw.trim() ? JSON.parse(raw) : { error: `Worker vide (${response.status})` }; }
    catch { body = { error: `Réponse worker invalide (${response.status})` }; }
    return NextResponse.json(body, { status: response.ok ? 200 : response.status });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "Worker inaccessible" }, { status: 502 });
  }
}

export async function OPTIONS() { return NextResponse.json({ ok: true }); }

export async function HEAD(request: Request) {
  const workerUrl = process.env.WORKER_URL;
  const workerKey = process.env.WORKER_API_KEY;
  if (!workerUrl || !workerKey) return new Response(null, { status: 503 });
  const response = await callWorker(`${workerUrl.replace(/\/$/, "")}/rainfall/output.xlsx`, { headers: { "X-API-Key": workerKey } });
  return new Response(null, { status: response.status });
}
