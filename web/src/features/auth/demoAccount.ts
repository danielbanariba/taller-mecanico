import type { LoginPayload } from "./api";

/**
 * The shared demo account of the public test deployment, or `null` for any
 * other build. Its credentials come from `VITE_DEMO_PHONE` and
 * `VITE_DEMO_PASSWORD`, which Vite compiles into the public JS bundle, so
 * they must only ever be set for that demo (see `deploy/demo/README.md`).
 *
 * Read on every call rather than at module load, so tests can stub the env.
 */
export function getDemoAccount(): LoginPayload | null {
  const phone = import.meta.env.VITE_DEMO_PHONE;
  const password = import.meta.env.VITE_DEMO_PASSWORD;
  if (!phone || !password) {
    return null;
  }
  return { phone, password };
}
