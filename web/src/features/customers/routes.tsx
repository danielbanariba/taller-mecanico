import type { RouteObject } from "react-router";

import { CustomersPage } from "./CustomersPage";
import { EditCustomerPage } from "./EditCustomerPage";
import { NewCustomerPage } from "./NewCustomerPage";

/**
 * Phase-1 customer routes, nested under the app shell's `/clientes` slot
 * (see `web/src/app/router.tsx`). The `/clientes/:customerId` detail route
 * and every vehicle route join this tree in Slice 5.
 */
export const customerRoutes: RouteObject[] = [
  { index: true, element: <CustomersPage /> },
  { path: "nuevo", element: <NewCustomerPage /> },
  { path: ":customerId/editar", element: <EditCustomerPage /> },
];
