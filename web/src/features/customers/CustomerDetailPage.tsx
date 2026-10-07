import { useNavigate, useParams } from "react-router";

import { ApiError } from "../../shared/api/http";
import { Alert } from "../../shared/ui/Alert";
import { Button } from "../../shared/ui/Button";
import { LinkButton } from "../../shared/ui/LinkButton";
import { Spinner } from "../../shared/ui/Spinner";
import { customersCopy, getCustomersErrorMessage } from "./copy";
import { useCustomer, useVehiclesForCustomer } from "./hooks";
import { VehicleList } from "./VehicleList";

/**
 * Container: a customer's own detail screen, reached from the customers
 * list. Lists that customer's vehicles (phase 1); their orders join this
 * page in phase 2. Reads come from the persisted query cache, so a
 * previously visited customer still renders offline.
 */
export function CustomerDetailPage() {
  const { customerId: id } = useParams<{ customerId: string }>();
  const customerId = id ?? "";
  const navigate = useNavigate();

  const customer = useCustomer(customerId);
  const vehicles = useVehiclesForCustomer(customerId);

  if (customer.isPending) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Spinner />
      </div>
    );
  }

  // A failed refetch keeps the cached customer; only the server saying the
  // customer is gone replaces it (same rule `ItemDetailPage` uses).
  const isNotFound = customer.error instanceof ApiError && customer.error.status === 404;
  if (isNotFound || !customer.data) {
    const errorCode = customer.error instanceof ApiError ? customer.error.code : "customer_not_found";
    return (
      <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-4 px-4 py-8">
        <Alert variant="error">{getCustomersErrorMessage(errorCode)}</Alert>
        <LinkButton to="/clientes" variant="secondary">
          {customersCopy.detail.backToList}
        </LinkButton>
      </main>
    );
  }

  const data = customer.data;

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-6 px-4 py-8">
      <header className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold text-brand-primary">{data.full_name}</h1>
        {data.phone ? (
          <p className="text-base text-brand-muted-foreground">
            {data.phone}
            {data.phone_is_mobile === true
              ? ` · ${customersCopy.list.mobileBadge}`
              : data.phone_is_mobile === false
                ? ` · ${customersCopy.list.landlineBadge}`
                : ""}
          </p>
        ) : null}
      </header>

      <LinkButton to={`/clientes/${customerId}/editar`} variant="secondary">
        {customersCopy.detail.editCustomer}
      </LinkButton>

      <section className="flex flex-col gap-3">
        <h2 className="text-xl font-semibold text-brand-foreground">{customersCopy.detail.vehiclesTitle}</h2>
        <Button onClick={() => navigate(`/clientes/${customerId}/vehiculos/nuevo`)}>
          {customersCopy.detail.addVehicle}
        </Button>
        {vehicles.isPending ? (
          <div className="flex justify-center py-8">
            <Spinner />
          </div>
        ) : (
          <VehicleList
            vehicles={vehicles.data ?? []}
            onOpen={(vehicle) => navigate(`/clientes/${customerId}/vehiculos/${vehicle.id}`)}
          />
        )}
      </section>
    </main>
  );
}
