import { useState } from "react";
import { useNavigate, useParams } from "react-router";

import { ApiError } from "../../shared/api/http";
import { useOnlineStatus } from "../../shared/offline/useOnlineStatus";
import { customersCopy, getCustomersErrorMessage } from "./copy";
import { useCreateVehicle } from "./hooks";
import { VehicleForm, type VehicleFormValues } from "./VehicleForm";

/** Container: wires the shared vehicle form to the create mutation and routing, under one customer. */
export function NewVehiclePage() {
  const { customerId: id } = useParams<{ customerId: string }>();
  const customerId = id ?? "";
  const navigate = useNavigate();
  const isOffline = useOnlineStatus();
  const [vehicleId] = useState(() => crypto.randomUUID());
  const createVehicle = useCreateVehicle(customerId);

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
