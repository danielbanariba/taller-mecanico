import { createBrowserRouter, Navigate, Outlet } from "react-router";

import { LoginPage } from "../features/auth/LoginPage";
import { RegisterPage } from "../features/auth/RegisterPage";
import { EditItemPage } from "../features/inventory/EditItemPage";
import { InventoryPage } from "../features/inventory/InventoryPage";
import { ItemDetailPage } from "../features/inventory/ItemDetailPage";
import { NewItemPage } from "../features/inventory/NewItemPage";
import { RequireSession } from "./RequireSession";

export const router = createBrowserRouter([
  { path: "/", element: <Navigate to="/inventario" replace /> },
  { path: "/login", element: <LoginPage /> },
  { path: "/registro", element: <RegisterPage /> },
  {
    path: "/inventario",
    element: (
      <RequireSession>
        <Outlet />
      </RequireSession>
    ),
    children: [
      { index: true, element: <InventoryPage /> },
      { path: "nuevo", element: <NewItemPage /> },
      { path: ":id", element: <ItemDetailPage /> },
      { path: ":id/editar", element: <EditItemPage /> },
    ],
  },
]);
