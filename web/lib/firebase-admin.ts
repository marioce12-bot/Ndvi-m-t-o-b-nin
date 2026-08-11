import { cert, getApps, initializeApp } from "firebase-admin/app";
import { getFirestore } from "firebase-admin/firestore";

export function getAdminDb() {
  if (!getApps().length) {
    const raw = process.env.FIREBASE_SERVICE_ACCOUNT_JSON;
    if (!raw) throw new Error("FIREBASE_SERVICE_ACCOUNT_JSON is not configured");
    const serviceAccount = JSON.parse(raw);
    initializeApp({ credential: cert(serviceAccount) });
  }
  return getFirestore();
}
