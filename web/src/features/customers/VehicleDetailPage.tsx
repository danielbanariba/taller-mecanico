import { useParams } from "react-router";

import { ApiError } from "../../shared/api/http";
import { Alert } from "../../shared/ui/Alert";
import { LinkButton } from "../../shared/ui/LinkButton";
import { Spinner } from "../../shared/ui/Spinner";
import { customersCopy, getCustomersErrorMessage } from "./copy";
import { useVehicle } from "./hooks";

/**
 * Container: a single vehicle's detail screen, showing its owner. Service
 * orders join this page in phase 2. Reads come from the persisted query
 * cache, so a previously visited vehicle still renders offline.
 */
export function VehicleDetailPage() {
  const { vehicleId: id } = useParams<{ vehicleId: string }>();
  const vehicleId = id ?? "";

  const vehicle = useVehicle(vehicleId);

  if (vehicle.isPending) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Spinner />
      </div>
    );
  }

  // A failed refetch keeps the cached vehicle; only the server saying the
  // vehicle is gone replaces it (same rule `ItemDetailPage` uses).
  const isNotFound = vehicle.error instanceof ApiError && vehicle.error.status === 404;
  if (isNotFound || !vehicle.data) {
    const errorCode = vehicle.error instanceof ApiError ? vehicle.error.code : "vehicle_not_found";
    return (
      <div className="flex flex-col gap-4">
        <Alert variant="error">{getCustomersErrorMessage(errorCode)}</Alert>
        <LinkButton to="/clientes" variant="secondary">
          {customersCopy.detail.backToList}
        </LinkButton>
      </div>
    );
  }

  const data = vehicle.data;

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold text-brand-primary">
          {[data.make, data.model].filter(Boolean).join(" ")}
        </h1>
        <p className="text-base text-brand-muted-foreground">
          {customersCopy.vehicles.typeLabels[data.vehicle_type]}
          {data.plate ? ` · ${data.plate}` : ""}
          {data.year ? ` · ${data.year}` : ""}
        </p>
        {data.color ? <p className="text-base text-brand-muted-foreground">{data.color}</p> : null}
      </header>

      <LinkButton to={`/clientes/${data.customer_id}`} variant="secondary">
        {`${customersCopy.vehicles.detail.ownerPrefix} ${data.owner.full_name}`}
      </LinkButton>

      <LinkButton to={`/clientes/${data.customer_id}/vehiculos/${vehicleId}/editar`}>
        {customersCopy.vehicles.detail.editVehicle}
      </LinkButton>

      {data.notes ? <p className="text-base text-brand-foreground">{data.notes}</p> : null}
    </div>
  );
}
