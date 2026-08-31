import { NextResponse } from "next/server";
import { hasPlatformSession, PLATFORM_COOKIE } from "@/lib/platform-auth";

export const runtime = "nodejs";

export async function GET(request: Request) {
  const cookie = request.headers.get("cookie")?.split(";").map((value) => value.trim()).find((value) => value.startsWith(`${PLATFORM_COOKIE}=`))?.slice(PLATFORM_COOKIE.length + 1);
  return NextResponse.json({ authenticated: hasPlatformSession(cookie) }, { status: hasPlatformSession(cookie) ? 200 : 401 });
}
