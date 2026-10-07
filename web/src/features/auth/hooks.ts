import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError } from "../../shared/api/http";
import { idbPersister } from "../../shared/offline/idbPersister";
import { authApi, type LoginPayload, type Me, type RegisterPayload } from "./api";

export const sessionQueryKey = ["auth", "session"] as const;

/**
 * A 401 is the server's definitive answer "not logged in", not a failure,
 * so it resolves to `null` instead of throwing. As data it replaces any
 * cached session (a persisted one included) rather than sitting next to it
 * as an error, which is what lets `RequireSession` tell "logged out" apart
 * from "can't reach the server" even while a cached session exists.
 */
async function fetchSession(): Promise<Me | null> {
  try {
    return await authApi.me();
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      return null;
    }
    throw error;
  }
}

/**
 * The current session, resolved from the httpOnly cookie via `GET
 * /api/auth/me`: a `Me`, or `null` once the server says it is not logged
 * in (see `fetchSession`). `retry: false` matters here: a network failure
 * should leave the cached session in place right away instead of keeping
 * `RequireSession` waiting out retries.
 */
export function useSession() {
  return useQuery({
    queryKey: sessionQueryKey,
    queryFn: fetchSession,
    retry: false,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: LoginPayload) => authApi.login(payload),
    onSuccess: (me: Me) => {
      queryClient.setQueryData(sessionQueryKey, me);
    },
  });
}

export function useRegister() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: RegisterPayload) => authApi.register(payload),
    onSuccess: (me: Me) => {
      queryClient.setQueryData(sessionQueryKey, me);
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => authApi.logout(),
    onSuccess: async () => {
      // Clears both layers: the in-memory QueryClient cache (so the next
      // `useSession` read refetches instead of serving the now-stale
      // cached user) and the persisted IndexedDB cache (so a different
      // workshop logging in on this same phone never sees the previous
      // one's inventory, even offline, before its own data loads).
      queryClient.clear();
      await idbPersister.removeClient();
    },
  });
}
