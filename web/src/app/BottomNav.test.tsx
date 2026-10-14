import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";

import { appCopy } from "./copy";
import { BottomNav } from "./BottomNav";

describe("BottomNav", () => {
  it("renders a decorative icon above each tab, keeping the accessible name as the Spanish label", () => {
    // Defect this catches: an icon added without aria-hidden (or carrying
    // its own accessible name, e.g. a <title>) would leak into the tab's
    // accessible name and break every `getByRole("link", { name: ... })`
    // query this app's other suites rely on; a tab missing its icon
    // markup entirely would also go undetected without this check.
    render(
      <MemoryRouter initialEntries={["/inventario"]}>
        <BottomNav />
      </MemoryRouter>,
    );

    for (const label of [appCopy.nav.inventario, appCopy.nav.clientes, appCopy.nav.ordenes]) {
      const link = screen.getByRole("link", { name: label });
      const icon = link.querySelector("svg");
      expect(icon).not.toBeNull();
      expect(icon).toHaveAttribute("aria-hidden", "true");
    }
  });

  it("keeps aria-current=page on only the active tab once the icon markup wraps the label", () => {
    // Defect this catches: wrapping the label in the new icon/pill markup
    // breaking NavLink's function-as-children wiring (e.g. swapping it
    // for a plain anchor, or hardcoding the pill on the wrong branch),
    // which would silently drop `aria-current` from every route -- a
    // real risk introduced by refactoring this exact render path.
    render(
      <MemoryRouter initialEntries={["/clientes/c1"]}>
        <BottomNav />
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: appCopy.nav.clientes })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: appCopy.nav.inventario })).not.toHaveAttribute("aria-current");
    expect(screen.getByRole("link", { name: appCopy.nav.ordenes })).not.toHaveAttribute("aria-current");
  });
});
