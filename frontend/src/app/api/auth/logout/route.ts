import { NextResponse } from "next/server";
import { EXPIRES_COOKIE, SESSION_COOKIE, expiresCookieOptions, sessionCookieOptions } from "@/lib/session";

export async function POST() {
  const response = NextResponse.json({ ok: true });
  response.cookies.set(SESSION_COOKIE, "", sessionCookieOptions(0));
  response.cookies.set(EXPIRES_COOKIE, "", expiresCookieOptions(0));
  return response;
}
