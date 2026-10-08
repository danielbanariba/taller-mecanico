import type { RouteObject } from "react-router";

/**
 * Invoicing's own slot inside the app shell's `/ordenes` tab
 * (`design.md`'s AD-15), spread into `workOrderRoutes`' children after
 * them (`web/src/app/router.tsx`), following the `caja` precedent:
 * lazy, since most workshops never open it, and nested through a flat
 * slash-separated `path` the same way `customers/routes.tsx` nests
 * vehicle routes under their customer.
 */
export const invoicingShellRoutes: RouteObject[] = [
  {
    path: "facturacion",
    lazy: async () => ({
      Component: (await import("./settings/InvoicingSettingsPage")).InvoicingSettingsPage,
    }),
  },
  {
    path: "facturacion/datos",
    lazy: async () => ({
      Component: (await import("./settings/FiscalProfilePage")).FiscalProfilePage,
    }),
  },
  {
    path: "facturacion/rangos/nuevo",
    lazy: async () => ({
      Component: (await import("./settings/CaiRangePage")).CaiRangePage,
    }),
  },
  {
    path: "facturacion/rangos/:rangeId",
    lazy: async () => ({
      Component: (await import("./settings/CaiRangePage")).CaiRangePage,
    }),
  },
  {
    path: ":orderId/factura/:invoiceId",
    lazy: async () => ({
      Component: (await import("./documents/InvoiceDetailPage")).InvoiceDetailPage,
    }),
  },
];
