import { NextResponse } from "next/server";
import { getAdminDb } from "@/lib/firebase-admin";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const product = new URL(request.url).searchParams.get("product") ?? "anomaly";
  try {
    const db = getAdminDb();
    const snapshot = await db.collection("pentadeCatalog").doc(product).get();
    if (snapshot.exists) return NextResponse.json({ pentades: snapshot.data()?.pentades ?? [] });

    // One server-side bootstrap for a brand-new product cache. Normal visits
    // use Firestore; the daily cron keeps the catalog fresh afterwards.
    const workerUrl = process.env.WORKER_URL;
    const workerKey = process.env.WORKER_API_KEY;
    if (!workerUrl || !workerKey) return NextResponse.json({ pentades: [], error: "Catalogue en attente de synchronisation" });
    const response = await fetch(`${workerUrl.replace(/\/$/, "")}/pentades?product=${encodeURIComponent(product)}`, { headers: { "X-API-Key": workerKey }, cache: "no-store" });
    if (!response.ok) return NextResponse.json({ pentades: [], error: "Catalogue FEWS NET indisponible" }, { status: 503 });
    const body = await response.json() as { pentades?: Array<Record<string, unknown>> };
    const pentades = Array.isArray(body.pentades) ? body.pentades : [];
    await db.collection("pentadeCatalog").doc(product).set({ pentades, updatedAt: new Date() });
    return NextResponse.json({ pentades });
  } catch (error) {
    console.error("Pentade catalog error", error);
    return NextResponse.json({ error: "Catalogue indisponible", pentades: [] }, { status: 503 });
  }
}
