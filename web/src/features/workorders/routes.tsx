import type { RouteObject } from "react-router";

import { NewWorkOrderPage } from "./NewWorkOrderPage";
import { WorkOrderDetailPage } from "./WorkOrderDetailPage";
import { WorkOrdersPage } from "./WorkOrdersPage";

/**
 * Phase-2 work-order routes, nested under the app shell's `/ordenes` slot
 * (see `web/src/app/router.tsx`), replacing the phase-1 "Próximamente"
 * placeholder. `nueva` is a literal segment matched before the `:orderId`
 * dynamic one, per `design.md`'s route tree. Payment/receipt routes arrive
 * in a later phase.
 */
export const workOrderRoutes: RouteObject[] = [
  { index: true, element: <WorkOrdersPage /> },
  { path: "nueva", element: <NewWorkOrderPage /> },
  { path: ":orderId", element: <WorkOrderDetailPage /> },
];
