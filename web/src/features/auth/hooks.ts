import { useMutation, useQuery, useQueryClient, type QueryClient, type QueryKey } from "@tanstack/react-query";

import { ApiError } from "../../shared/api/http";
import { idbPersister } from "../../shared/offline/idbPersister";
import { authApi, type LoginPayload, type Me, type RegisterPayload } from "./api";

export const sessionQueryKey = ["auth", "session"] as const;

const WORKSHOP_SCOPE = "workshop";

/**
 * Prefix for every query key holding one workshop's data (inventory today,
 * customers or work orders later), so a cached query always says which
 * workshop it belongs to. Two workshops' data can then never share a cache
 * entry, and `startSession` can drop everything that is not the new
 * session's.
 */
export function workshopQueryKey(workshopId: string | undefined) {
  return [WORKSHOP_SCOPE, workshopId] as const;
}

function isSessionKey(queryKey: QueryKey): boolean {
  return queryKey.length === sessionQueryKey.length && sessionQueryKey.every((part, index) => queryKey[index] === part);
}

function belongsToWorkshop(queryKey: QueryKey, workshopId: string): boolean {
  return queryKey[0] === WORKSHOP_SCOPE && queryKey[1] === workshopId;
}

/**
 * Stores the session a login or registration just started, after removing
 * every cached query that is not provably this workshop's: another
 * workshop's data, and anything not scoped to a workshop at all. The
 * session query itself is kept (and overwritten) so a screen observing it
 * keeps observing the same query. The persisted cache follows on its own:
 * `PersistQueryClientProvider` rewrites the whole IndexedDB snapshot from
 * memory on every cache change, these removals included. The outbox is
 * separate and untouched -- its entries carry their workshop id and still
 * sync when that workshop logs in again.
 */
function startSession(queryClient: QueryClient, me: Me): void {
  queryClient.removeQueries({
    predicate: (query) => !isSessionKey(query.queryKey) && !belongsToWorkshop(query.queryKey, me.workshop.id),
  });
  queryClient.setQueryData(sessionQueryKey, me);
}

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

/** The current session's workshop id, or undefined before it resolves. */
export function useWorkshopId(): string | undefined {
  const session = useSession();
  return session.data?.workshop.id;
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: LoginPayload) => authApi.login(payload),
    onSuccess: (me: Me) => startSession(queryClient, me),
  });
}

export function useRegister() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: RegisterPayload) => authApi.register(payload),
    onSuccess: (me: Me) => startSession(queryClient, me),
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
