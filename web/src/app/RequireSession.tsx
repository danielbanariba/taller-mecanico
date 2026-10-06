import type { ReactNode } from "react";
import { Navigate } from "react-router";

import { useSession } from "../features/auth/hooks";
import { Spinner } from "../shared/ui/Spinner";

export interface RequireSessionProps {
  children: ReactNode;
}

/** Route guard: redirects to /login when the session cannot be resolved. */
export function RequireSession({ children }: RequireSessionProps) {
  const session = useSession();

  if (session.isPending) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (session.isError) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
