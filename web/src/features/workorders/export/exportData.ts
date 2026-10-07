import { ApiError } from "../../../shared/api/http";

/** Used only if the server's `Content-Disposition` cannot be parsed. */
const FALLBACK_FILENAME = "taller-export.zip";

function filenameFromContentDisposition(header: string | null): string {
  const match = header ? /filename="([^"]+)"/.exec(header) : null;
  return match?.[1] ?? FALLBACK_FILENAME;
}

/**
 * Downloads "Exportar todo" (`design.md`'s "Export download" sequence):
 * fetches the ZIP, turns the response body into an object URL, clicks a
 * temporary `<a download>` on it, then revokes the URL right after the
 * click -- an object URL kept alive longer than that just leaks memory,
 * since nothing else in the app ever reads it again.
 *
 * Never called while offline -- the caller (the app shell's "Más" menu)
 * disables the trigger -- but `fetch` itself still maps a connection
 * failure to the same `network_error` code every other feature's
 * `ApiError` uses, instead of letting a raw `TypeError` escape.
 */
export async function exportData(): Promise<void> {
  let response: Response;
  try {
    response = await fetch("/api/export", { credentials: "same-origin" });
  } catch {
    throw new ApiError(0, "network_error");
  }

  if (!response.ok) {
    // A 401 means the session expired mid-visit; every other feature's
    // `copy.ts` already maps `not_authenticated` to the same "sign in
    // again" message (AD-16/"Export download"'s "existing session-expired
    // handling"). Anything else is reported as a generic export failure.
    throw new ApiError(response.status, response.status === 401 ? "not_authenticated" : "export_failed");
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filenameFromContentDisposition(response.headers.get("Content-Disposition"));
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
