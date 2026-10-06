import { createBrowserRouter, Navigate } from "react-router";

import { LoginPage } from "../features/auth/LoginPage";
import { RegisterPage } from "../features/auth/RegisterPage";
import { InventoryPage } from "../features/inventory/InventoryPage";
import { RequireSession } from "./RequireSession";

export const router = createBrowserRouter([
  { path: "/", element: <Navigate to="/inventario" replace /> },
  { path: "/login", element: <LoginPage /> },
  { path: "/registro", element: <RegisterPage /> },
  {
    path: "/inventario",
    element: (
      <RequireSession>
        <InventoryPage />
      </RequireSession>
    ),
  },
]);
