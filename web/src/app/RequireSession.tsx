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
 * Route guard. Only the server saying "not logged in" (a 401, which
 * `useSession` turns into `null` data) redirects to /login -- even when a
 * session is cached, since an expired or revoked session can never send
 * anything. Not reaching the server never redirects: if `session.data` is
 * still set (a cached session, whether restored from the persisted query
 * cache or just stale after a failed background refetch -- TanStack Query
 * keeps the previous `data` when a refetch fails), the protected content
 * renders anyway. Offline with no cached session at all shows a dedicated
 * "sin conexión" screen instead of the login form, which the user could
 * fill in and submit for nothing. That covers both ways the session check
 * can be offline: a request that failed (`network_error`), and one TanStack
 * Query paused because its `onlineManager` saw the browser's `offline`
 * event -- a paused check stays `pending` until the connection returns, so
 * it must not be treated as "still loading" or the spinner never ends.
 */
export function RequireSession({ children }: RequireSessionProps) {
  const session = useSession();
  const isPaused = session.fetchStatus === "paused";

  if (session.isPending && !isPaused) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (session.data === null) {
    return <Navigate to="/login" replace />;
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
  if (isNetworkError || isPaused) {
    return (
      <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-2 px-4 py-8 text-center">
        <h1 className="text-2xl font-bold text-brand-primary">{authCopy.offline.title}</h1>
        <p className="text-base text-brand-muted-foreground">{authCopy.offline.body}</p>
      </main>
    );
  }

  return <Navigate to="/login" replace />;
}
