import { useState } from "react";
import { useNavigate, useParams } from "react-router";

import { ApiError } from "../../shared/api/http";
import { useOnlineStatus } from "../../shared/offline/useOnlineStatus";
import { Alert } from "../../shared/ui/Alert";
import { LinkButton } from "../../shared/ui/LinkButton";
import { Spinner } from "../../shared/ui/Spinner";
import { customersCopy, getCustomersErrorMessage } from "./copy";
import { useCreateVehicle, useCustomer } from "./hooks";
import { VehicleForm, type VehicleFormValues } from "./VehicleForm";

/** Container: wires the shared vehicle form to the create mutation and routing, under one customer. */
export function NewVehiclePage() {
  const { customerId: id } = useParams<{ customerId: string }>();
  const customerId = id ?? "";
  const navigate = useNavigate();
  const isOffline = useOnlineStatus();
  const [vehicleId] = useState(() => crypto.randomUUID());
  const customer = useCustomer(customerId);
  const createVehicle = useCreateVehicle(customerId);

  if (customer.isPending) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Spinner />
      </div>
    );
  }

  // Reached directly by URL for an archived customer: the API rejects a
  // new vehicle for an archived owner with `customer_archived`, so this
  // screen must show that instead of a form that would just fail on
  // submit (a QA sweep finding -- the generic 404 the API returned before
  // this fix looked like the owner did not exist at all).
  if (customer.data?.archived_at != null) {
    return (
      <div className="flex flex-col gap-4">
        <Alert variant="info">{customersCopy.archivedNotice}</Alert>
        <LinkButton to={`/clientes/${customerId}`} variant="secondary">
          {customersCopy.vehicles.create.backToDetail}
        </LinkButton>
      </div>
    );
  }

  function handleSubmit(values: VehicleFormValues) {
    createVehicle.mutate(
      {
        id: vehicleId,
        customer_id: customerId,
        vehicle_type: values.vehicleType,
        make: values.make,
        model: values.model || undefined,
        year: values.year ?? undefined,
        color: values.color || undefined,
        plate: values.plate || undefined,
        notes: values.notes || undefined,
      },
      {
        onSuccess: () => navigate(`/clientes/${customerId}`, { replace: true }),
      },
    );
  }

  const errorMessage =
    createVehicle.error instanceof ApiError ? getCustomersErrorMessage(createVehicle.error.code) : undefined;

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-3xl font-bold text-brand-primary">{customersCopy.vehicles.create.title}</h1>
      <LinkButton to={`/clientes/${customerId}`} variant="secondary">
        {customersCopy.vehicles.create.backToDetail}
      </LinkButton>
      <VehicleForm
        mode="create"
        onSubmit={handleSubmit}
        pending={createVehicle.isPending}
        errorMessage={errorMessage}
        submitLabel={customersCopy.vehicles.create.submit}
        submitPendingLabel={customersCopy.vehicles.create.submitPending}
        offline={isOffline}
      />
    </div>
  );
}
