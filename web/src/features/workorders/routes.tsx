import type { RouteObject } from "react-router";

import { WorkOrderDetailPage } from "./WorkOrderDetailPage";
import { WorkOrdersPage } from "./WorkOrdersPage";

/**
 * Phase-2 work-order routes, nested under the app shell's `/ordenes` slot
 * (see `web/src/app/router.tsx`), replacing the phase-1 "Próximamente"
 * placeholder. New-order and payment/receipt routes arrive in later
 * slices.
 */
export const workOrderRoutes: RouteObject[] = [
  { index: true, element: <WorkOrdersPage /> },
  { path: ":orderId", element: <WorkOrderDetailPage /> },
];
