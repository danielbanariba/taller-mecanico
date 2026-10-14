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
 *
 * `main`'s bottom padding reads `--bottom-nav-height` and
 * `--sync-toast-height` (both published by `BottomNav`/`OfflineStatusBanner`
 * via `useCssHeightVariable`) instead of a fixed `pb-20`: a QA sweep found
 * that literal left the last inventory row's stock buttons partly covered
 * by the sync toast, worse once a pending change grew it to two lines. The
 * `5rem`/`0px` fallbacks keep the old, pre-measurement padding until both
 * variables are published.
 */
export function AppShell() {
  const navigate = useNavigate();
  const session = useSession();
  const logout = useLogout();
  const isOffline = useOnlineStatus();
  const [moreOpen, setMoreOpen] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | undefined>(undefined);
  const [logoutError, setLogoutError] = useState<string | undefined>(undefined);

  function handleLogout() {
    setLogoutError(undefined);
    logout.mutate(undefined, {
      onSuccess: () => navigate("/login", { replace: true }),
      onError: (error) => {
        setLogoutError(getAppErrorMessage(error instanceof ApiError ? error.code : "unknown_error"));
      },
    });
  }

  function openMore() {
    setExportError(undefined);
    setLogoutError(undefined);
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
        {/* `fullWidth={false}` keeps this content-width instead of `Button`'s
            default full-bleed sizing; `!min-h-11`/`!text-base` need the `!`
            important modifier to win over `Button`'s own `min-h-12`/`text-lg`
            -- Tailwind has no class-merging, so a plain conflicting class
            loses to whichever rule the generated stylesheet orders later.
            `min-h-11` (44px) is the accessible tap-target floor; the
            previous `min-h-10` (40px) fell short of it. */}
        <Button
          variant="secondary"
          onClick={openMore}
          fullWidth={false}
          className="!min-h-11 px-4 !text-base"
        >
          {appCopy.more.trigger}
        </Button>
      </header>
      <main className="mx-auto flex w-full max-w-md flex-1 flex-col gap-4 px-4 pb-[calc(var(--bottom-nav-height,5rem)+var(--sync-toast-height,0px)+1rem)]">
        <Outlet />
      </main>
      <BottomNav />

      <Dialog open={moreOpen} title={appCopy.more.title} onClose={() => setMoreOpen(false)}>
        <div className="flex flex-col gap-3">
          <LinkButton to="/ordenes/caja" variant="secondary" onClick={() => setMoreOpen(false)}>
            {appCopy.more.cashSummary}
          </LinkButton>

          {/* Visible regardless of fiscal-profile state (`fiscal-profile`
              spec's "The menu entry is visible with no profile yet"): it is
              also the only way to reach the form that creates the first one. */}
          <LinkButton to="/ordenes/facturacion" variant="secondary" onClick={() => setMoreOpen(false)}>
            {appCopy.more.invoicing}
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

          {isOffline ? <Alert variant="info">{appCopy.logout.offlineDisabled}</Alert> : null}
          {logoutError ? <Alert variant="error">{logoutError}</Alert> : null}
          <Button
            variant="destructive"
            onClick={handleLogout}
            loading={logout.isPending}
            disabled={isOffline || logout.isPending}
          >
            {appCopy.logout.submit}
          </Button>
        </div>
      </Dialog>
    </div>
  );
}
