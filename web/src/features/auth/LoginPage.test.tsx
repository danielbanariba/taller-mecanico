import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { server } from "../../test/server";
import { LoginPage } from "./LoginPage";

const ME_RESPONSE = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

function renderLoginPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/inventario" element={<div>Pantalla de inventario</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

async function fillAndSubmit(user: ReturnType<typeof userEvent.setup>, password: string) {
  await user.type(screen.getByLabelText(/teléfono/i), "99998888");
  await user.type(screen.getByLabelText(/contraseña/i), password);
  await user.click(screen.getByRole("button", { name: /iniciar sesión/i }));
}

describe("LoginPage", () => {
  it("navigates to /inventario after a successful login", async () => {
    server.use(http.post("/api/auth/login", () => HttpResponse.json(ME_RESPONSE, { status: 200 })));
    const user = userEvent.setup();
    renderLoginPage();

    await fillAndSubmit(user, "password123");

    expect(await screen.findByText("Pantalla de inventario")).toBeInTheDocument();
  });

  it("shows the Spanish message for invalid_credentials on a 401", async () => {
    server.use(
      http.post("/api/auth/login", () => HttpResponse.json({ detail: "invalid_credentials" }, { status: 401 })),
    );
    const user = userEvent.setup();
    renderLoginPage();

    await fillAndSubmit(user, "wrong-password");

    expect(await screen.findByText("Teléfono o contraseña incorrectos.")).toBeInTheDocument();
  });

  it("tells the user to wait, not that the password is wrong, when the phone is locked out", async () => {
    server.use(
      http.post("/api/auth/login", () =>
        HttpResponse.json(
          { detail: "too_many_login_attempts" },
          { status: 429, headers: { "Retry-After": "900" } },
        ),
      ),
    );
    const user = userEvent.setup();
    renderLoginPage();

    await fillAndSubmit(user, "password123");

    expect(
      await screen.findByText("Demasiados intentos fallidos. Espere unos minutos e intente de nuevo."),
    ).toBeInTheDocument();
  });

  it("disables the submit button while the login request is pending", async () => {
    server.use(http.post("/api/auth/login", () => new Promise<Response>(() => {})));
    const user = userEvent.setup();
    renderLoginPage();

    const submitButton = screen.getByRole("button", { name: /iniciar sesión/i });
    await user.type(screen.getByLabelText(/teléfono/i), "99998888");
    await user.type(screen.getByLabelText(/contraseña/i), "password123");
    await user.click(submitButton);

    expect(submitButton).toBeDisabled();
  });

  describe("demo account", () => {
    afterEach(() => {
      vi.unstubAllEnvs();
    });

    it("prefills the demo credentials, explains them, and logs in with exactly those", async () => {
      vi.stubEnv("VITE_DEMO_PHONE", "9999-9999");
      vi.stubEnv("VITE_DEMO_PASSWORD", "demo1234");
      let sentBody: unknown;
      server.use(
        http.post("/api/auth/login", async ({ request }) => {
          sentBody = await request.json();
          return HttpResponse.json(ME_RESPONSE, { status: 200 });
        }),
      );
      const user = userEvent.setup();
      renderLoginPage();

      expect(screen.getByLabelText(/teléfono/i)).toHaveValue("9999-9999");
      expect(screen.getByLabelText(/contraseña/i)).toHaveValue("demo1234");
      expect(screen.getByText(/cuenta de demostración/i)).toBeInTheDocument();

      await user.click(screen.getByRole("button", { name: /iniciar sesión/i }));

      expect(await screen.findByText("Pantalla de inventario")).toBeInTheDocument();
      expect(sentBody).toEqual({ phone: "9999-9999", password: "demo1234" });
    });

    it("leaves the form empty and shows no demo notice when the demo account is not configured", () => {
      // Stubbed to undefined rather than left alone, so a shell that happens
      // to export VITE_DEMO_* cannot make this production guard pass or fail.
      vi.stubEnv("VITE_DEMO_PHONE", undefined);
      vi.stubEnv("VITE_DEMO_PASSWORD", undefined);
      renderLoginPage();

      expect(screen.getByLabelText(/teléfono/i)).toHaveValue("");
      expect(screen.getByLabelText(/contraseña/i)).toHaveValue("");
      expect(screen.queryByText(/cuenta de demostración/i)).not.toBeInTheDocument();
    });
  });
});
