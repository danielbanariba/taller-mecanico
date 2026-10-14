import { createBrowserRouter, Navigate, Outlet, type RouteObject } from "react-router";

import { LoginPage } from "../features/auth/LoginPage";
import { RegisterPage } from "../features/auth/RegisterPage";
import { customerRoutes } from "../features/customers/routes";
import { ArchivedItemsPage } from "../features/inventory/ArchivedItemsPage";
import { EditItemPage } from "../features/inventory/EditItemPage";
import { InventoryPage } from "../features/inventory/InventoryPage";
import { ItemDetailPage } from "../features/inventory/ItemDetailPage";
import { NewItemPage } from "../features/inventory/NewItemPage";
import { invoicingShellRoutes } from "../features/invoicing/routes";
import { workOrderRoutes } from "../features/workorders/routes";
import { AppErrorBoundary } from "./AppErrorBoundary";
import { AppShell } from "./AppShell";
import { NotFoundPage } from "./NotFoundPage";
import { RequireSession } from "./RequireSession";

/**
 * Exported separately from `router` (not only passed inline to
 * `createBrowserRouter`) so a test can build its own `createMemoryRouter`
 * from the exact same route tree -- including the trailing catch-all below
 * -- instead of asserting against `NotFoundPage` rendered in isolation,
 * which stays green even if this route array's `path: "*"` entry is
 * removed entirely.
 */
export const appRoutes: RouteObject[] = [
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
              { path: "archivados", element: <ArchivedItemsPage /> },
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
          // Catch-all for any URL that matches nothing above: a static
          // path always outranks this splat regardless of declaration
          // order, so it only ever catches a genuinely unknown route.
          // Nested here (not as a sibling of `RequireSession`'s own
          // children) so a logged-in user sees it inside `AppShell`,
          // with the bottom nav and header still reachable.
          { path: "*", element: <NotFoundPage /> },
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
      // The Factura's own print routes (`fiscal-document-print` spec),
      // siblings of the receipt routes above for the same reason (AD-16):
      // no navigation chrome ever prints, and a workshop that never
      // prints a Factura never downloads this chunk.
      {
        path: "/ordenes/:orderId/factura/:invoiceId/58mm",
        lazy: async () => ({
          Component: (await import("../features/invoicing/print/Invoice58Page")).Invoice58Page,
        }),
      },
      {
        path: "/ordenes/:orderId/factura/:invoiceId/carta",
        lazy: async () => ({
          Component: (await import("../features/invoicing/print/InvoiceLetterPage")).InvoiceLetterPage,
        }),
      },
      // The Nota de Crédito's own print routes (`fiscal-document-print`
      // spec, Phase B requirement), siblings of the Factura's print
      // routes above for the same reason (AD-16).
      {
        path: "/ordenes/:orderId/nota-credito/:creditNoteId/58mm",
        lazy: async () => ({
          Component: (await import("../features/invoicing/print/CreditNote58Page")).CreditNote58Page,
        }),
      },
      {
        path: "/ordenes/:orderId/nota-credito/:creditNoteId/carta",
        lazy: async () => ({
          Component: (await import("../features/invoicing/print/CreditNoteLetterPage")).CreditNoteLetterPage,
        }),
      },
    ],
  },
];

export const router = createBrowserRouter(appRoutes);
