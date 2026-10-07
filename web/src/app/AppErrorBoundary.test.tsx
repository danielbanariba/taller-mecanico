import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";

import { idbPersister } from "../shared/offline/idbPersister";
import { AppErrorBoundary } from "./AppErrorBoundary";

function ThrowingScreen(): never {
  throw new Error("boom");
}

function renderThrowingRoute() {
  const router = createMemoryRouter(
    [{ path: "/", element: <ThrowingScreen />, errorElement: <AppErrorBoundary /> }],
    { initialEntries: ["/"] },
  );
  return render(<RouterProvider router={router} />);
}

afterEach(() => {
  Reflect.deleteProperty(window, "location");
});

describe("AppErrorBoundary", () => {
  it("renders the Spanish message instead of react-router's default error page", async () => {
    // Defect this catches: a render crash anywhere in the protected tree
    // falling through to react-router's own "Unexpected Application
    // Error!" screen, in English, with a raw stack trace -- unreadable
    // to this app's users.
    renderThrowingRoute();

    expect(await screen.findByRole("heading", { name: "Algo salió mal" })).toBeInTheDocument();
    expect(screen.queryByText(/Unexpected Application Error/i)).not.toBeInTheDocument();
  });

  it("reloads the app when the user clicks the reload button", async () => {
    // Defect this catches: the reload button rendering but not actually
    // reloading the page, leaving the user stuck on the crashed screen.
    const reload = vi.fn();
    Object.defineProperty(window, "location", {
      value: { ...window.location, reload },
      writable: true,
      configurable: true,
    });
    const user = userEvent.setup();
    renderThrowingRoute();

    await user.click(await screen.findByRole("button", { name: "Recargar" }));

    await vi.waitFor(() => expect(reload).toHaveBeenCalledTimes(1));
  });

  it("drops the persisted query cache before reloading", async () => {
    // Defect this catches: a crash caused by a cached response the code no
    // longer understands. Reloading alone rehydrates the same cache and
    // crashes again, so the user can never leave this screen.
    const reload = vi.fn();
    Object.defineProperty(window, "location", {
      value: { ...window.location, reload },
      writable: true,
      configurable: true,
    });
    const removeClient = vi.spyOn(idbPersister, "removeClient");
    const user = userEvent.setup();
    renderThrowingRoute();

    await user.click(await screen.findByRole("button", { name: "Recargar" }));

    await vi.waitFor(() => expect(reload).toHaveBeenCalledTimes(1));
    expect(removeClient).toHaveBeenCalledTimes(1);
    expect(removeClient.mock.invocationCallOrder[0]).toBeLessThan(reload.mock.invocationCallOrder[0]);
    removeClient.mockRestore();
  });
});
