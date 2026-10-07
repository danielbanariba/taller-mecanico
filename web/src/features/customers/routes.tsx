import type { RouteObject } from "react-router";

import { CustomerDetailPage } from "./CustomerDetailPage";
import { CustomersPage } from "./CustomersPage";
import { EditCustomerPage } from "./EditCustomerPage";
import { EditVehiclePage } from "./EditVehiclePage";
import { NewCustomerPage } from "./NewCustomerPage";
import { NewVehiclePage } from "./NewVehiclePage";
import { VehicleDetailPage } from "./VehicleDetailPage";

/**
 * Phase-1 customer and vehicle routes, nested under the app shell's
 * `/clientes` slot (see `web/src/app/router.tsx`). Vehicle URLs nest under
 * their owning customer (AD-16), so the active bottom-nav tab stays
 * simply the first path segment.
 */
export const customerRoutes: RouteObject[] = [
  { index: true, element: <CustomersPage /> },
  { path: "nuevo", element: <NewCustomerPage /> },
  { path: ":customerId", element: <CustomerDetailPage /> },
  { path: ":customerId/editar", element: <EditCustomerPage /> },
  { path: ":customerId/vehiculos/nuevo", element: <NewVehiclePage /> },
  { path: ":customerId/vehiculos/:vehicleId", element: <VehicleDetailPage /> },
  { path: ":customerId/vehiculos/:vehicleId/editar", element: <EditVehiclePage /> },
];
