import type { ComponentType } from "react";
import { NavLink } from "react-router";

import { CustomersIcon } from "../shared/ui/icons/CustomersIcon";
import { InventoryIcon } from "../shared/ui/icons/InventoryIcon";
import { WorkOrdersIcon } from "../shared/ui/icons/WorkOrdersIcon";
import { useCssHeightVariable } from "../shared/ui/useCssHeightVariable";
import { appCopy } from "./copy";

interface NavItemProps {
  to: string;
  label: string;
  icon: ComponentType<{ className?: string }>;
}

function navLabelClassName({ isActive }: { isActive: boolean }): string {
  return `flex min-h-12 flex-1 flex-col items-center justify-center gap-0.5 py-1 text-xs transition-colors ${
    isActive ? "font-bold text-brand-primary" : "font-medium text-brand-muted-foreground"
  }`;
}

/**
 * The icon's own background pill: filled and tinted only while its tab
 * is active, so the active tab reads as unmistakable without relying on
 * the label's text color alone (`navLabelClassName` above still carries
 * that color change too, as a second, independent cue).
 */
function navIconWrapperClassName(isActive: boolean): string {
  return `flex h-7 w-12 items-center justify-center rounded-full transition-colors ${
    isActive ? "bg-brand-accent text-brand-on-accent" : "text-brand-muted-foreground"
  }`;
}

function NavItem({ to, label, icon: Icon }: NavItemProps) {
  return (
    <NavLink to={to} className={navLabelClassName}>
      {({ isActive }) => (
        <>
          <span className={navIconWrapperClassName(isActive)}>
            <Icon className="h-5 w-5" />
          </span>
          {label}
        </>
      )}
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
 * own, so the active tab needs no extra wiring here. The active tab is
 * never marked by color alone: its icon sits on a filled pill and its
 * label turns bold, both driven by the same `isActive` NavLink reports.
 *
 * Publishes its own rendered height (`useCssHeightVariable`, safe-area
 * padding included) as `--bottom-nav-height` on `document.documentElement`,
 * so `AppShell`'s `<main>` padding and `OfflineStatusBanner`'s own offset
 * both measure the real nav instead of a hand-copied literal (a QA sweep
 * found the hardcoded `3rem` guess was off by about 6px). The variable
 * resets to `0px` when this unmounts, since the receipt and print routes
 * render no bottom nav at all.
 */
export function BottomNav() {
  const navRef = useCssHeightVariable<HTMLElement>("--bottom-nav-height");

  return (
    <nav
      ref={navRef}
      aria-label={appCopy.nav.label}
      className="fixed inset-x-0 bottom-0 flex border-t border-brand-border bg-brand-card pb-[env(safe-area-inset-bottom)]"
    >
      <NavItem to="/inventario" label={appCopy.nav.inventario} icon={InventoryIcon} />
      <NavItem to="/clientes" label={appCopy.nav.clientes} icon={CustomersIcon} />
      <NavItem to="/ordenes" label={appCopy.nav.ordenes} icon={WorkOrdersIcon} />
    </nav>
  );
}
