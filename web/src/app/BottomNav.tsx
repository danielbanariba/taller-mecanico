import { NavLink } from "react-router";

import { appCopy } from "./copy";

interface NavItemProps {
  to: string;
  label: string;
}

function navItemClassName({ isActive }: { isActive: boolean }): string {
  return `flex min-h-12 flex-1 flex-col items-center justify-center text-xs font-medium transition-colors ${
    isActive ? "text-brand-primary" : "text-brand-muted-foreground"
  }`;
}

function NavItem({ to, label }: NavItemProps) {
  return (
    <NavLink to={to} className={navItemClassName}>
      {label}
    </NavLink>
  );
}

/**
 * Presentational bottom navigation: three destinations, each at least
 * 48px tall (the Material Design minimum tap target). Fixed to the
 * viewport bottom and padded for the iOS/Android home-indicator safe
 * area, so it never covers -- nor sits under -- a destination's own
 * content. `NavLink`'s default (non-`end`) matching marks a tab active
 * for every route nested under it and sets `aria-current="page"` on its
 * own, so the active tab needs no extra wiring here.
 */
export function BottomNav() {
  return (
    <nav
      aria-label={appCopy.nav.label}
      className="fixed inset-x-0 bottom-0 flex border-t border-brand-border bg-brand-card pb-[env(safe-area-inset-bottom)]"
    >
      <NavItem to="/inventario" label={appCopy.nav.inventario} />
      <NavItem to="/clientes" label={appCopy.nav.clientes} />
      <NavItem to="/ordenes" label={appCopy.nav.ordenes} />
    </nav>
  );
}
