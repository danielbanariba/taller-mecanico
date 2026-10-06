import type { ReactNode } from "react";
import { Navigate } from "react-router";

import { authCopy } from "../features/auth/copy";
import { useSession } from "../features/auth/hooks";
import { OfflineStatusBanner } from "../features/inventory/OfflineStatusBanner";
import { ApiError } from "../shared/api/http";
import { Spinner } from "../shared/ui/Spinner";

export interface RequireSessionProps {
  children: ReactNode;
}

/**
 * Route guard. A `network_error` never redirects to /login by itself: if
 * `session.data` is still set (a cached session, whether restored from the
 * persisted query cache or just stale after a failed background refetch --
 * see `src/shared/api/http.ts` / TanStack Query's error-state handling,
 * which keeps the previous `data` around when a refetch fails), the
 * protected content renders anyway. Only a real 401 ("not logged in", not
 * "can't reach the server right now") redirects. Offline with no cached
 * session at all shows a dedicated "sin conexión" screen instead of
 * silently sending the user to the login form, which they could fill in
 * and submit for nothing.
 */
export function RequireSession({ children }: RequireSessionProps) {
  const session = useSession();

  if (session.isPending) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (session.data) {
    return (
      <>
        <OfflineStatusBanner workshopId={session.data.workshop.id} />
        {children}
      </>
    );
  }

  const isNetworkError = session.error instanceof ApiError && session.error.code === "network_error";
  if (isNetworkError) {
    return (
      <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-2 px-4 py-8 text-center">
        <h1 className="text-2xl font-bold text-brand-primary">{authCopy.offline.title}</h1>
        <p className="text-base text-brand-muted-foreground">{authCopy.offline.body}</p>
      </main>
    );
  }

  return <Navigate to="/login" replace />;
}
