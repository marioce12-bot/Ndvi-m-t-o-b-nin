import { NextResponse } from "next/server";

export function POST() {
  return NextResponse.json({ error: "Generation API not implemented yet" }, { status: 501 });
}
