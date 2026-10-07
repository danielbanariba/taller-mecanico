import { createBrowserRouter, Navigate, Outlet } from "react-router";

import { LoginPage } from "../features/auth/LoginPage";
import { RegisterPage } from "../features/auth/RegisterPage";
import { customerRoutes } from "../features/customers/routes";
import { EditItemPage } from "../features/inventory/EditItemPage";
import { InventoryPage } from "../features/inventory/InventoryPage";
import { ItemDetailPage } from "../features/inventory/ItemDetailPage";
import { NewItemPage } from "../features/inventory/NewItemPage";
import { WorkOrdersComingSoon } from "../features/workorders/WorkOrdersComingSoon";
import { AppShell } from "./AppShell";
import { RequireSession } from "./RequireSession";

export const router = createBrowserRouter([
  { path: "/", element: <Navigate to="/inventario" replace /> },
  { path: "/login", element: <LoginPage /> },
  { path: "/registro", element: <RegisterPage /> },
  {
    // Pathless: guards every tab screen below without adding a path
    // segment. `AppShell` nests right under it so the bottom nav and
    // logout render for every one of them.
    element: (
      <RequireSession>
        <Outlet />
      </RequireSession>
    ),
    children: [
      {
        element: <AppShell />,
        children: [
          {
            path: "/inventario",
            children: [
              { index: true, element: <InventoryPage /> },
              { path: "nuevo", element: <NewItemPage /> },
              { path: ":id", element: <ItemDetailPage /> },
              { path: ":id/editar", element: <EditItemPage /> },
            ],
          },
          {
            // "/clientes/:customerId" (detail) and every vehicle route
            // land in Slice 5.
            path: "/clientes",
            children: customerRoutes,
          },
          { path: "/ordenes", element: <WorkOrdersComingSoon /> },
        ],
      },
    ],
  },
]);
