import { Outlet, useNavigate } from "react-router";

import { useLogout, useSession } from "../features/auth/hooks";
import { Button } from "../shared/ui/Button";
import { BottomNav } from "./BottomNav";
import { appCopy } from "./copy";

/**
 * Layout route rendered above every protected screen: the workshop name
 * and the logout action (moved here from `InventoryPage`, so no page
 * duplicates it), the active screen's own content, and the bottom
 * navigation. `main` is padded at the bottom so its last row is never
 * hidden behind the fixed nav.
 */
export function AppShell() {
  const navigate = useNavigate();
  const session = useSession();
  const logout = useLogout();

  function handleLogout() {
    logout.mutate(undefined, {
      onSuccess: () => navigate("/login", { replace: true }),
    });
  }

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="mx-auto flex w-full max-w-md flex-col gap-3 px-4 py-6">
        <h1 className="text-2xl font-bold text-brand-primary">{session.data?.workshop.name}</h1>
        <Button variant="secondary" onClick={handleLogout} loading={logout.isPending}>
          {appCopy.logout.submit}
        </Button>
      </header>
      <main className="mx-auto flex w-full max-w-md flex-1 flex-col gap-4 px-4 pb-20">
        <Outlet />
      </main>
      <BottomNav />
    </div>
  );
}
