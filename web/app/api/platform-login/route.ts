import { NextResponse } from "next/server";
import { isPlatformPassword, PLATFORM_COOKIE, sessionValue } from "@/lib/platform-auth";

export const runtime = "nodejs";

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  if (!isPlatformPassword(String(body.password ?? ""))) return NextResponse.json({ error: "Mot de passe incorrect" }, { status: 401 });
  const response = NextResponse.json({ ok: true });
  response.cookies.set(PLATFORM_COOKIE, sessionValue(), { httpOnly: true, secure: process.env.NODE_ENV === "production", sameSite: "lax", path: "/", maxAge: 60 * 60 * 24 * 30 });
  return response;
}

export async function DELETE() {
  const response = NextResponse.json({ ok: true });
  response.cookies.delete(PLATFORM_COOKIE);
  return response;
}
