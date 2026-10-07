import type { RouteObject } from "react-router";

import { NewWorkOrderPage } from "./NewWorkOrderPage";
import { WorkOrderDetailPage } from "./WorkOrderDetailPage";
import { WorkOrdersPage } from "./WorkOrdersPage";

/**
 * Phase-2/3 work-order routes, nested under the app shell's `/ordenes`
 * slot (see `web/src/app/router.tsx`), replacing the phase-1
 * "Próximamente" placeholder. `nueva` and `caja` are literal segments
 * matched before the `:orderId` dynamic one, per `design.md`'s route
 * tree -- `caja` is lazy (AD-16's "Lazy loading" note: a mechanic who
 * never opens the cash summary never downloads its chunk), rendered
 * inside this same `<AppShell>` (unlike the receipt routes, which sit
 * outside it as `router.tsx` siblings).
 */
export const workOrderRoutes: RouteObject[] = [
  { index: true, element: <WorkOrdersPage /> },
  { path: "nueva", element: <NewWorkOrderPage /> },
  {
    path: "caja",
    lazy: async () => ({
      Component: (await import("./cash/CashSummaryPage")).CashSummaryPage,
    }),
  },
  { path: ":orderId", element: <WorkOrderDetailPage /> },
];
