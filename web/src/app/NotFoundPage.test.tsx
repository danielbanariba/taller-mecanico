import { render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { createMemoryRouter, RouterProvider } from "react-router";

import { server } from "../test/server";
import { appCopy } from "./copy";
import { AppProviders } from "./providers";
import { appRoutes } from "./router";

const SESSION = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

function mockSession() {
  server.use(http.get("/api/auth/me", () => HttpResponse.json(SESSION)));
}

/**
 * Builds the router from `router.tsx`'s own exported `appRoutes` array --
 * the exact tree the real app mounts -- instead of rendering `NotFoundPage`
 * in isolation. Rendering the component alone stays green even if
 * `router.tsx`'s trailing `{ path: "*", element: <NotFoundPage /> }` route
 * were deleted entirely; going through the real route configuration does
 * not.
 */
function renderAppAt(path: string) {
  const router = createMemoryRouter(appRoutes, { initialEntries: [path] });
  return render(
    <AppProviders>
      <RouterProvider router={router} />
    </AppProviders>,
  );
}

describe("NotFoundPage", () => {
  it("shows the Spanish not-found message instead of react-router's default page for an unknown route", async () => {
    // Defect this catches: removing the catch-all route from `router.tsx`
    // (or react-router simply finding no match for an unknown URL) falls
    // through to react-router's own "Unexpected Application Error! 404 Not
    // Found" page, in English, with no way back into the app. The previous
    // version of this test rendered `<NotFoundPage />` directly and stayed
    // green even with that route deleted, since it never went through
    // `router.tsx` at all.
    mockSession();
    renderAppAt("/esto-no-existe");

    expect(await screen.findByRole("heading", { name: appCopy.notFound.title })).toBeInTheDocument();
    expect(screen.queryByText(/Unexpected Application Error/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/404/)).not.toBeInTheDocument();
  });

  it("links back to the inventory", async () => {
    // Defect this catches: a mechanic landing on an unknown URL with no way
    // back into the app other than the browser's own back button.
    mockSession();
    renderAppAt("/esto-no-existe");

    const link = await screen.findByRole("link", { name: appCopy.notFound.backLink });
    expect(link).toHaveAttribute("href", "/inventario");
  });
});
