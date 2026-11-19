import { NextResponse, type NextRequest } from "next/server";
import { apiBaseUrl, setSessionCookies } from "@/lib/session";

type SignUp = { organization_name: string; full_name: string; email: string; password: string };

async function post(path: string, body: unknown) {
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  const data = await response.json().catch(() => ({ detail: "Unexpected response from the server" }));
  return { response, data };
}

export async function POST(request: NextRequest) {
  const signUp = (await request.json().catch(() => null)) as SignUp | null;
  if (!signUp) return NextResponse.json({ detail: "Invalid request data" }, { status: 422 });

  try {
    const created = await post("/auth/register", signUp);
    if (!created.response.ok) return NextResponse.json(created.data, { status: created.response.status });

    const login = await post("/auth/login", { email: signUp.email, password: signUp.password });
    if (!login.response.ok) return NextResponse.json(login.data, { status: login.response.status });

    const response = NextResponse.json({ ok: true }, { status: 201 });
    setSessionCookies(response.cookies, login.data);
    return response;
  } catch {
    return NextResponse.json({ detail: "The server cannot be reached. Please try again shortly." }, { status: 503 });
  }
}
