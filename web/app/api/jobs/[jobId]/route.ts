import { NextResponse } from "next/server";
import { getSupabaseAdmin, verifyRequestUser } from "@/lib/supabase-admin";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(_request: Request, context: { params: Promise<{ jobId: string }> }) {
  try {
    const { jobId } = await context.params;
    const user = await verifyRequestUser(_request);
    const { data, error } = await getSupabaseAdmin().from("jobs").select("*").eq("id", jobId).maybeSingle();
    if (error) throw error;
    if (!data) return NextResponse.json({ error: "Job introuvable" }, { status: 404 });
    if (user.id !== "platform" && data.owner_id !== user.id) return NextResponse.json({ error: "Accès interdit" }, { status: 403 });
    return NextResponse.json({
      id: data.id, product: data.product, pentadeId: data.pentade_id, label: data.label ?? data.pentade_id,
      status: data.status, progress: Number(data.progress ?? 0), step: data.step ?? "", url: data.image_url, imageUrl: data.image_url, thumbnailUrl: data.thumbnail_url, error: data.error,
    });
  } catch (error) {
    console.error("Job route error", error);
    return NextResponse.json({ error: error instanceof Error && error.message === "AUTH_REQUIRED" ? "Authentification requise" : "Supabase indisponible" }, { status: error instanceof Error && error.message === "AUTH_REQUIRED" ? 401 : 503 });
  }
}
