export type FieldError = { field: string; message: string };

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
    readonly fieldErrors: FieldError[] = [],
  ) {
    super(message);
  }

  /** Field errors keyed by the last part of the field path, e.g. "body.score" -> "score". */
  get byField(): Record<string, string> {
    const result: Record<string, string> = {};
    for (const error of this.fieldErrors) {
      const key = error.field.split(".").at(-1) ?? error.field;
      result[key] ??= error.message;
    }
    return result;
  }
}

const BASE = "/api/backend";

function messageFor(status: number, detail: unknown): string {
  if (typeof detail === "string" && detail) return detail;
  if (status === 403) return "You do not have permission to do this.";
  if (status === 404) return "The record was not found. It may have been removed.";
  if (status >= 500) return "Something went wrong on the server. Please try again.";
  return "The request could not be completed.";
}

let redirecting = false;

function goToLogin() {
  if (redirecting || typeof window === "undefined") return;
  redirecting = true;
  const next = `${window.location.pathname}${window.location.search}`;
  window.location.assign(next === "/" ? "/login" : `/login?next=${encodeURIComponent(next)}`);
}

/**
 * Set by the app shell. Called when the session has ended; resolves `true` once the user has
 * signed in again (the request is then retried), or `false` if they chose to sign out.
 */
type ReauthHandler = () => Promise<boolean>;
let reauthHandler: ReauthHandler | null = null;
let reauthInProgress: Promise<boolean> | null = null;

export function setReauthHandler(handler: ReauthHandler | null) {
  reauthHandler = handler;
}

function reauthenticate(): Promise<boolean> {
  if (!reauthHandler) {
    goToLogin();
    return Promise.resolve(false);
  }
  reauthInProgress ??= reauthHandler().finally(() => {
    reauthInProgress = null;
  });
  return reauthInProgress;
}

type Query = Record<string, string | number | boolean | null | undefined>;

export function withQuery(path: string, query?: Query): string {
  if (!query) return path;
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null && value !== "") params.set(key, String(value));
  }
  const text = params.toString();
  return text ? `${path}?${text}` : path;
}

type RequestOptions = { method?: string; body?: unknown; query?: Query };

export async function api<T>(path: string, { method = "GET", body, query }: RequestOptions = {}): Promise<T> {
  const init: RequestInit = { method, headers: { Accept: "application/json" } };
  if (body instanceof FormData) {
    init.body = body;
  } else if (body !== undefined) {
    init.body = JSON.stringify(body);
    (init.headers as Record<string, string>)["Content-Type"] = "application/json";
  }

  const send = async () => {
    try {
      return await fetch(withQuery(`${BASE}${path}`, query), init);
    } catch {
      throw new ApiError(0, "Network error. Check your connection and try again.");
    }
  };

  let response = await send();
  if (response.status === 401) {
    // Session ended: sign in again in place (the page and any typed form data stay), then retry once.
    if (!(await reauthenticate())) throw new ApiError(401, "Your session has ended. Please sign in again.");
    response = await send();
    if (response.status === 401) {
      goToLogin();
      throw new ApiError(401, "Your session has ended. Please sign in again.");
    }
  }
  if (response.status === 204) return undefined as T;

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(response.status, messageFor(response.status, data?.detail), data?.errors ?? []);
  }
  return data as T;
}

/** SWR fetcher: the key is the backend path with its query string. */
export const fetcher = <T>(path: string) => api<T>(path);

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return "Something went wrong. Please try again.";
}
