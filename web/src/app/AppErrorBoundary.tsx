import { Button } from "../shared/ui/Button";
import { appCopy } from "./copy";

/**
 * `router.tsx`'s `errorElement` at the root of the protected route tree.
 * Without it, an unexpected render error (a crash in any screen under
 * `RequireSession`) falls through to react-router's own default error
 * page: "Unexpected Application Error!", in English, with a raw stack
 * trace -- meaningless and unreadable to this app's Spanish-speaking
 * users. This renders a short, actionable Spanish message instead.
 *
 * Deliberately does not render the error itself (no `useRouteError()`
 * output shown): a stack trace is still not something a mechanic can act
 * on, and the error is already visible in the browser console for
 * debugging. Renders outside `AppShell` (no bottom nav), since the crash
 * may be inside the shell itself.
 */
export function AppErrorBoundary() {
  function handleReload() {
    window.location.reload();
  }

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-4 p-6 text-center">
      <h1 className="text-2xl font-bold text-brand-primary">{appCopy.error.title}</h1>
      <p className="text-base text-brand-foreground">{appCopy.error.message}</p>
      <Button onClick={handleReload} className="w-auto px-6">
        {appCopy.error.reload}
      </Button>
    </div>
  );
}
