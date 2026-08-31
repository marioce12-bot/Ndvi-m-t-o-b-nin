import { createHmac, timingSafeEqual } from "node:crypto";

export const PLATFORM_COOKIE = "meteo_platform_session";

function secret() {
  return process.env.PLATFORM_ACCESS_PASSWORD ?? "";
}

function digest(value: string) {
  return createHmac("sha256", secret()).update(value).digest("hex");
}

export function isPlatformPassword(value: string) {
  const expected = secret();
  if (!expected || !value) return false;
  const actualBuffer = Buffer.from(digest(value));
  const expectedBuffer = Buffer.from(digest(expected));
  return actualBuffer.length === expectedBuffer.length && timingSafeEqual(actualBuffer, expectedBuffer);
}

export function sessionValue() {
  return digest("authenticated-platform-session");
}

export function hasPlatformSession(cookieValue?: string) {
  if (!cookieValue || !secret()) return false;
  const actual = Buffer.from(cookieValue);
  const expected = Buffer.from(sessionValue());
  return actual.length === expected.length && timingSafeEqual(actual, expected);
}
