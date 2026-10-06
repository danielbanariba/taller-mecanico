import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { server } from "../../test/server";
import { RegisterPage } from "./RegisterPage";

function renderRegisterPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/registro"]}>
        <Routes>
          <Route path="/registro" element={<RegisterPage />} />
          <Route path="/inventario" element={<div>Pantalla de inventario</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

async function fillForm(user: ReturnType<typeof userEvent.setup>, password: string) {
  await user.type(screen.getByLabelText(/nombre del taller/i), "Taller Ana");
  await user.type(screen.getByLabelText(/nombre del propietario/i), "Ana Pérez");
  await user.type(screen.getByLabelText(/teléfono/i), "99998888");
  await user.type(screen.getByLabelText(/contraseña/i), password);
  await user.click(screen.getByRole("button", { name: /crear cuenta/i }));
}

describe("RegisterPage", () => {
  it("shows the Spanish message for phone_already_registered on a 409", async () => {
    server.use(
      http.post("/api/auth/register", () =>
        HttpResponse.json({ detail: "phone_already_registered" }, { status: 409 }),
      ),
    );
    const user = userEvent.setup();
    renderRegisterPage();

    await fillForm(user, "password123");

    expect(await screen.findByText("Ese número de teléfono ya está registrado.")).toBeInTheDocument();
  });

  it("blocks submission for a password shorter than 8 characters without calling the API", async () => {
    let apiWasCalled = false;
    server.use(
      http.post("/api/auth/register", () => {
        apiWasCalled = true;
        return HttpResponse.json({ detail: "unexpected" }, { status: 500 });
      }),
    );
    const user = userEvent.setup();
    renderRegisterPage();

    await fillForm(user, "short1");

    expect(
      await screen.findByText("La contraseña debe tener al menos 8 caracteres."),
    ).toBeInTheDocument();
    expect(apiWasCalled).toBe(false);
  });
});
