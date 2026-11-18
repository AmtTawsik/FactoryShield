import "server-only";

export const SESSION_COOKIE = "fs_token";
/** Readable by the page (holds only the expiry time) so it can warn before the session ends. */
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
