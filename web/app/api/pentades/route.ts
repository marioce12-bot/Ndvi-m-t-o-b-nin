import { NextResponse } from "next/server";
import { getAdminDb } from "@/lib/firebase-admin";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const product = new URL(request.url).searchParams.get("product") ?? "anomaly";
  try {
    const db = getAdminDb();
    const snapshot = await db.collection("pentadeCatalog").doc(product).get();
    if (snapshot.exists) return NextResponse.json({ pentades: snapshot.data()?.pentades ?? [] });
    return NextResponse.json({ pentades: [], error: "Catalogue en attente de synchronisation automatique" });
  } catch (error) {
    console.error("Pentade catalog error", error);
    return NextResponse.json({ error: "Catalogue indisponible", pentades: [] }, { status: 503 });
  }
}
