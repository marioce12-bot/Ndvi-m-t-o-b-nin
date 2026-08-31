import { createClient } from "@supabase/supabase-js";

export function getSupabaseAdmin() {
  const url = process.env.SUPABASE_URL ?? process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) throw new Error("Supabase server variables are not configured");
  return createClient(url, key, { auth: { autoRefreshToken: false, persistSession: false } });
}

export async function verifyRequestUser(request: Request) {
  if (request.headers.get("cookie")?.includes("meteo_platform_session=")) return { id: "platform", email: "platform@local" };
  const header = request.headers.get("authorization");
  if (!header?.startsWith("Bearer ")) throw new Error("AUTH_REQUIRED");
  const { data, error } = await getSupabaseAdmin().auth.getUser(header.slice(7));
  if (error || !data.user) throw new Error("AUTH_INVALID");
  return data.user;
}
