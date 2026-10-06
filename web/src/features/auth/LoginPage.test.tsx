import { describe, expect, it } from "vitest";
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
});
