import { createBrowserRouter, Navigate, Outlet } from "react-router";

import { LoginPage } from "../features/auth/LoginPage";
import { RegisterPage } from "../features/auth/RegisterPage";
import { customerRoutes } from "../features/customers/routes";
import { EditItemPage } from "../features/inventory/EditItemPage";
import { InventoryPage } from "../features/inventory/InventoryPage";
import { ItemDetailPage } from "../features/inventory/ItemDetailPage";
import { NewItemPage } from "../features/inventory/NewItemPage";
import { invoicingShellRoutes } from "../features/invoicing/routes";
import { workOrderRoutes } from "../features/workorders/routes";
import { AppErrorBoundary } from "./AppErrorBoundary";
import { AppShell } from "./AppShell";
import { RequireSession } from "./RequireSession";

export const router = createBrowserRouter([
  { path: "/", element: <Navigate to="/inventario" replace /> },
  { path: "/login", element: <LoginPage /> },
  { path: "/registro", element: <RegisterPage /> },
  {
    // Pathless: guards every tab screen below without adding a path
    // segment. `AppShell` nests right under it so the bottom nav and
    // logout render for every one of them. `errorElement` at this same
    // root catches any unexpected render error anywhere in the protected
    // tree (including inside `AppShell` itself) and shows a short
    // Spanish message instead of react-router's default English
    // developer error page.
    element: (
      <RequireSession>
        <Outlet />
      </RequireSession>
    ),
    errorElement: <AppErrorBoundary />,
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
            path: "/clientes",
            children: customerRoutes,
          },
          {
            path: "/ordenes",
            // Invoicing's own routes (`facturacion`, ...) are spread in
            // after `workOrderRoutes`, after the `caja` precedent
            // (`design.md`'s AD-15): static segments outrank `:orderId`
            // regardless of declaration order.
            children: [...workOrderRoutes, ...invoicingShellRoutes],
          },
        ],
      },
      // Receipt routes render without `AppShell` (`design.md`'s AD-16),
      // so no navigation chrome ever prints, while staying siblings of it
      // under the same `RequireSession` guard above. Lazy per AD-16's
      // "Lazy loading" note: a mechanic who never prints a receipt never
      // downloads this chunk.
      {
        path: "/ordenes/:orderId/recibo/58mm",
        lazy: async () => ({
          Component: (await import("../features/workorders/receipt/Receipt58Page")).Receipt58Page,
        }),
      },
      {
        path: "/ordenes/:orderId/recibo/carta",
        lazy: async () => ({
          Component: (await import("../features/workorders/receipt/ReceiptLetterPage")).ReceiptLetterPage,
        }),
      },
    ],
  },
]);
