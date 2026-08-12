import { NextResponse } from "next/server";
import { getAdminDb } from "@/lib/firebase-admin";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const snapshot = await getAdminDb().collection("jobs").where("status", "==", "done").limit(100).get();
    const jobs = snapshot.docs.map((item) => ({ id: item.id, ...item.data() })) as Array<{ id: string; completedAt?: { toMillis?: () => number } }>;
    jobs.sort((left, right) => {
      const leftTime = left.completedAt?.toMillis?.() ?? 0;
      const rightTime = right.completedAt?.toMillis?.() ?? 0;
      return rightTime - leftTime;
    }).slice(0, 24);
    return NextResponse.json({ jobs });
  } catch (error) {
    console.error("Jobs route error", error);
    return NextResponse.json({ error: "Firestore indisponible", jobs: [] }, { status: 503 });
  }
}
