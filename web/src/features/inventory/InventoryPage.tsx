import { useNavigate } from "react-router";

import { Button } from "../../shared/ui/Button";
import { authCopy } from "../auth/copy";
import { useLogout, useSession } from "../auth/hooks";
import { inventoryCopy } from "./copy";

/**
 * Placeholder for T5, which builds the real list/search/stepper screens.
 * For T4 this only proves the session guard and logout flow work end to end.
 */
export function InventoryPage() {
  const navigate = useNavigate();
  const session = useSession();
  const logout = useLogout();

  function handleLogout() {
    logout.mutate(undefined, {
      onSuccess: () => navigate("/login", { replace: true }),
    });
  }

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-6 px-4 py-8">
      <header>
        <p className="text-base text-brand-muted-foreground">{inventoryCopy.placeholder.greeting}</p>
        <h1 className="text-3xl font-bold text-brand-primary">{session.data?.workshop.name}</h1>
      </header>
      <Button variant="secondary" onClick={handleLogout} loading={logout.isPending}>
        {authCopy.logout.submit}
      </Button>
    </main>
  );
}
