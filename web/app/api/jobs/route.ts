import { NextResponse } from "next/server";
import { getSupabaseAdmin, verifyRequestUser } from "@/lib/supabase-admin";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  try {
    const user = await verifyRequestUser(request);
    const query = getSupabaseAdmin().from("jobs").select("*").eq("status", "done").order("completed_at", { ascending: false }).limit(24);
    const { data, error } = user.id === "platform" ? await query : await query.eq("owner_id", user.id);
    if (error) throw error;
    const jobs = (data ?? []).map((item) => ({ id: item.id, product: item.product, pentadeId: item.pentade_id, label: item.label, imageUrl: item.image_url, thumbnailUrl: item.thumbnail_url, completedAt: item.completed_at ? { _seconds: Math.floor(new Date(item.completed_at).getTime() / 1000) } : undefined }));
    return NextResponse.json({ jobs });
  } catch (error) {
    console.error("Jobs route error", error);
    return NextResponse.json({ error: error instanceof Error && error.message === "AUTH_REQUIRED" ? "Authentification requise" : "Supabase indisponible", jobs: [] }, { status: error instanceof Error && error.message === "AUTH_REQUIRED" ? 401 : 503 });
  }
}
