import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { idbPersister } from "../../shared/offline/idbPersister";
import { authApi, type LoginPayload, type Me, type RegisterPayload } from "./api";

export const sessionQueryKey = ["auth", "session"] as const;

/**
 * The current session, resolved from the httpOnly cookie via `GET
 * /api/auth/me`. `retry: false` matters here: a 401 means "not logged in",
 * not a transient failure, so retrying would only delay the redirect that
 * `RequireSession` performs on error.
 */
export function useSession() {
  return useQuery({
    queryKey: sessionQueryKey,
    queryFn: authApi.me,
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
