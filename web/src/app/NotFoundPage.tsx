import { LinkButton } from "../shared/ui/LinkButton";
import { appCopy } from "./copy";

/**
 * Catch-all screen for any URL that matches no route (`router.tsx`'s
 * trailing `path: "*"`), rendered inside `AppShell` for a logged-in user
 * so the bottom nav and header stay reachable. Without this, react-router
 * falls through to its own "Unexpected Application Error! 404 Not Found"
 * page, in English, with no way back into the app.
 */
export function NotFoundPage() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold text-brand-primary">{appCopy.notFound.title}</h1>
      <p className="text-base text-brand-muted-foreground">{appCopy.notFound.message}</p>
      <LinkButton to="/inventario" fullWidth={false} className="px-6">
        {appCopy.notFound.backLink}
      </LinkButton>
    </div>
  );
}
