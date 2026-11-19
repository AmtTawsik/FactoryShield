import "server-only";

export const SESSION_COOKIE = "fs_token";
export const EXPIRES_COOKIE = "fs_expires";

export function apiBaseUrl(): string {
  return (process.env.API_BASE_URL ?? "http://localhost:8000/api/v1").replace(/\/+$/, "");
}

export function expiresCookieOptions(maxAge: number) {
  return { ...sessionCookieOptions(maxAge), httpOnly: false };
}

export function sessionCookieOptions(maxAge: number) {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.COOKIE_SECURE === "true",
    path: "/",
    maxAge,
  };
}

type CookieJar = { set: (name: string, value: string, options: ReturnType<typeof sessionCookieOptions>) => void };

export function setSessionCookies(cookies: CookieJar, token: { access_token: string; expires_in: number }) {
  cookies.set(SESSION_COOKIE, token.access_token, sessionCookieOptions(token.expires_in));
  cookies.set(EXPIRES_COOKIE, String(Date.now() + token.expires_in * 1000), expiresCookieOptions(token.expires_in));
}
