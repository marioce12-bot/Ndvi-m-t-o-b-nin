import { NextResponse } from "next/server";
import { getSupabaseAdmin } from "@/lib/supabase-admin";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const product = new URL(request.url).searchParams.get("product") ?? "anomaly";
  try {
    const { data, error } = await getSupabaseAdmin().from("pentade_catalog").select("pentades").eq("product", product).maybeSingle();
    if (error) throw error;
    if (!data) return NextResponse.json({ pentades: [], error: "Catalogue en attente de la prochaine synchronisation" });
    return NextResponse.json({ pentades: data.pentades ?? [] });
  } catch (error) {
    console.error("Pentade catalog error", error);
    return NextResponse.json({ error: "Catalogue indisponible", pentades: [] }, { status: 503 });
  }
}
