import { useState } from "react";
import { Outlet, useNavigate } from "react-router";

import { useLogout, useSession } from "../features/auth/hooks";
import { ApiError } from "../shared/api/http";
import { useOnlineStatus } from "../shared/offline/useOnlineStatus";
import { Alert } from "../shared/ui/Alert";
import { Button } from "../shared/ui/Button";
import { Dialog } from "../shared/ui/Dialog";
import { LinkButton } from "../shared/ui/LinkButton";
import { BottomNav } from "./BottomNav";
import { appCopy, getAppErrorMessage } from "./copy";

/**
 * Layout route rendered above every protected screen: the workshop name
 * and a "Más" menu (the active screen's own content, and the bottom
 * navigation). The menu replaces phase 1's lone logout button with three
 * actions -- Caja del día, Exportar todo, Cerrar sesión -- behind the
 * shared `Dialog.tsx` pattern every other confirm/action sheet in this
 * app already uses, per `design.md`'s AD-16/File Changes note. `main` is
 * padded at the bottom so its last row is never hidden behind the fixed
 * nav.
 *
 * The workshop name renders as a styled `<p>`, not an `<h1>`: every nested
 * screen already renders its own `<h1>` for its page title, and a second
 * top-level heading here would leave the page with two `<h1>`s, which
 * breaks the single-top-level-heading landmark assistive tech relies on
 * to navigate the page.
 */
export function AppShell() {
  const navigate = useNavigate();
  const session = useSession();
  const logout = useLogout();
  const isOffline = useOnlineStatus();
  const [moreOpen, setMoreOpen] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | undefined>(undefined);

  function handleLogout() {
    logout.mutate(undefined, {
      onSuccess: () => navigate("/login", { replace: true }),
    });
  }

  function openMore() {
    setExportError(undefined);
    setMoreOpen(true);
  }

  // The dynamic `import()` keeps `exportData.ts` -- and the `zipfile`-style
  // blob/anchor/revoke plumbing it does not need anywhere else -- out of
  // the main chunk, per AD-16's "Lazy boundaries" note: a mechanic who
  // never exports never downloads this code.
  async function handleExport() {
    setExportError(undefined);
    setExporting(true);
    try {
      const { exportData } = await import("../features/workorders/export/exportData");
      await exportData();
      setMoreOpen(false);
    } catch (error) {
      setExportError(getAppErrorMessage(error instanceof ApiError ? error.code : "export_failed"));
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="mx-auto flex w-full max-w-md items-center justify-between gap-3 px-4 py-6">
        <p className="text-2xl font-bold text-brand-primary">{session.data?.workshop.name}</p>
        <Button variant="secondary" onClick={openMore} className="w-auto px-4">
          {appCopy.more.trigger}
        </Button>
      </header>
      <main className="mx-auto flex w-full max-w-md flex-1 flex-col gap-4 px-4 pb-20">
        <Outlet />
      </main>
      <BottomNav />

      <Dialog open={moreOpen} title={appCopy.more.title} onClose={() => setMoreOpen(false)}>
        <div className="flex flex-col gap-3">
          <LinkButton to="/ordenes/caja" variant="secondary" onClick={() => setMoreOpen(false)}>
            {appCopy.more.cashSummary}
          </LinkButton>

          {isOffline ? <Alert variant="info">{appCopy.more.exportOfflineDisabled}</Alert> : null}
          {exportError ? <Alert variant="error">{exportError}</Alert> : null}
          <Button
            variant="secondary"
            onClick={handleExport}
            loading={exporting}
            disabled={isOffline || exporting}
          >
            {exporting ? appCopy.more.exportPending : appCopy.more.exportAction}
          </Button>

          <Button variant="destructive" onClick={handleLogout} loading={logout.isPending}>
            {appCopy.logout.submit}
          </Button>
        </div>
      </Dialog>
    </div>
  );
}
