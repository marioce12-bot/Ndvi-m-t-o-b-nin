import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const tableDefinitions = [
  { id: "decades", title: "DECADES", description: "Entrée réseau pluviométrique : relevés journaliers par poste et par décade.", editable: true },
  { id: "agro", title: "RENSEIGNEMENTS AGRO", description: "Entrée stations synoptiques : observations météo par station et par jour.", editable: true },
  { id: "normales", title: "NORMALES", description: "Référentiels intégrés : normales pluviométriques RESA et normales agro-synoptiques.", editable: false },
  { id: "resa", title: "RESA-01", description: "Sortie automatisée calculée à partir des deux entrées et de l’historique.", editable: false },
] as const;

export function GET() {
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
  const formData = await request.formData();
  const source = formData.get("source");
  const file = formData.get("file");
  const workerUrl = process.env.WORKER_URL;
  const workerKey = process.env.WORKER_API_KEY;
  if (!(file instanceof File) || (source !== "decades" && source !== "agro")) {
    return NextResponse.json({ error: "Fichier ou source invalide" }, { status: 400 });
  }
  if (!workerUrl || !workerKey) {
    return NextResponse.json({ error: "WORKER_URL et WORKER_API_KEY doivent être configurées dans Vercel" }, { status: 503 });
  }
  const upstream = new FormData();
  upstream.set("file", file, file.name);
  const query = new URLSearchParams({ source: String(source) });
  for (const key of ["year", "month", "decade"]) {
    const value = formData.get(key);
    if (value) query.set(key, String(value));
  }
  const response = await fetch(`${workerUrl.replace(/\/$/, "")}/rainfall/import?${query.toString()}`, { method: "POST", headers: { "X-API-Key": workerKey }, body: upstream });
  const body = await response.json();
  return NextResponse.json(body, { status: response.status });
}

export async function PUT() {
  const workerUrl = process.env.WORKER_URL;
  const workerKey = process.env.WORKER_API_KEY;
  if (!workerUrl || !workerKey) return NextResponse.json({ error: "Worker non configuré" }, { status: 503 });
  const response = await fetch(`${workerUrl.replace(/\/$/, "")}/rainfall/imports`, { headers: { "X-API-Key": workerKey }, cache: "no-store" });
  const body = await response.json();
  return NextResponse.json(body, { status: response.status });
}
