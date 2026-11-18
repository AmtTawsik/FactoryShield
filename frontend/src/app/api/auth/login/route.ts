import { NextResponse, type NextRequest } from "next/server";
import { apiBaseUrl, setSessionCookies } from "@/lib/session";

type TokenResponse = { access_token: string; expires_in: number };

export async function POST(request: NextRequest) {
  let upstream: Response;
  try {
    upstream = await fetch(`${apiBaseUrl()}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: await request.text(),
      cache: "no-store",
    });
  } catch {
    return NextResponse.json({ detail: "The server cannot be reached. Please try again shortly." }, { status: 503 });
  }

  const body = await upstream.json().catch(() => ({ detail: "Unexpected response from the server" }));
  if (!upstream.ok) {
    return NextResponse.json(body, { status: upstream.status });
  }

  const token = body as TokenResponse;
  const response = NextResponse.json({ ok: true });
  setSessionCookies(response.cookies, token);
  return response;
}
