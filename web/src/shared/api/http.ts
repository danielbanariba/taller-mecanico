/**
 * Thin fetch wrapper shared by every feature's `api.ts`. It assumes the API
 * is reachable at the same origin (the Vite dev proxy forwards `/api` in
 * development; both are served from the same origin in production), so the
 * httpOnly session cookie is sent automatically — the client never touches
 * the token itself.
 */

export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

/**
 * Thrown for every failed request. `code` is the API's `detail` string
 * (e.g. "invalid_credentials") so callers can map it to user-facing copy,
 * or "network_error" when the request never reached the server.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string) {
    super(`API error ${status}: ${code}`);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

interface RequestOptions {
  method: HttpMethod;
  body?: unknown;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

async function readJsonBody(response: Response): Promise<unknown> {
  const text = await response.text();
  if (text.length === 0) {
    return undefined;
  }
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return undefined;
  }
}

async function request<T>(path: string, options: RequestOptions): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      method: options.method,
      credentials: "same-origin",
      headers: options.body !== undefined ? { "Content-Type": "application/json" } : undefined,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    });
  } catch {
    // fetch rejects on DNS/connection failures, CORS blocks, and offline.
    throw new ApiError(0, "network_error");
  }

  if (!response.ok) {
    const data = await readJsonBody(response);
    const detail = isRecord(data) ? data.detail : undefined;
    // FastAPI's own validation errors (422) put a list of issues in
    // `detail` instead of a string; every error this app raises on purpose
    // uses a string code, so a non-string detail falls back to a generic one.
    const code = typeof detail === "string" ? detail : "unknown_error";
    throw new ApiError(response.status, code);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await readJsonBody(response)) as T;
}

export const http = {
  get: <T>(path: string): Promise<T> => request<T>(path, { method: "GET" }),
  post: <T>(path: string, body?: unknown): Promise<T> => request<T>(path, { method: "POST", body }),
  put: <T>(path: string, body?: unknown): Promise<T> => request<T>(path, { method: "PUT", body }),
  patch: <T>(path: string, body?: unknown): Promise<T> => request<T>(path, { method: "PATCH", body }),
};
