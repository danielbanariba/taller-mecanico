import { useState } from "react";
import { useNavigate, useParams } from "react-router";

import { ApiError } from "../../shared/api/http";
import { useOnlineStatus } from "../../shared/offline/useOnlineStatus";
import { Alert } from "../../shared/ui/Alert";
import { Button } from "../../shared/ui/Button";
import { Dialog } from "../../shared/ui/Dialog";
import { LinkButton } from "../../shared/ui/LinkButton";
import { Spinner } from "../../shared/ui/Spinner";
import { customersCopy, getCustomersErrorMessage } from "./copy";
import { useArchiveVehicle, useUpdateVehicle, useVehicle } from "./hooks";
import { VehicleForm, type VehicleFormValues } from "./VehicleForm";
import type { UpdateVehiclePayload, VehicleDetailOut } from "./api";

/** Computes the minimal PATCH payload: only the fields the form actually changed. */
function diffVehicle(vehicle: VehicleDetailOut, values: VehicleFormValues): UpdateVehiclePayload {
  const payload: UpdateVehiclePayload = {};

  if (values.vehicleType !== vehicle.vehicle_type) {
    payload.vehicle_type = values.vehicleType;
  }
  if (values.make !== vehicle.make) {
    payload.make = values.make;
  }
  const originalModel = vehicle.model ?? "";
  if (values.model !== originalModel) {
    payload.model = values.model === "" ? null : values.model;
  }
  if (values.year !== vehicle.year) {
    payload.year = values.year;
  }
  const originalColor = vehicle.color ?? "";
  if (values.color !== originalColor) {
    payload.color = values.color === "" ? null : values.color;
  }
  const originalPlate = vehicle.plate ?? "";
  if (values.plate !== originalPlate) {
    payload.plate = values.plate === "" ? null : values.plate;
  }
  const originalNotes = vehicle.notes ?? "";
  if (values.notes !== originalNotes) {
    payload.notes = values.notes === "" ? null : values.notes;
  }

  return payload;
}

/** Container: wires the shared vehicle form to the update mutation, and owns archiving. */
export function EditVehiclePage() {
  const { customerId: cid, vehicleId: vid } = useParams<{ customerId: string; vehicleId: string }>();
  const customerId = cid ?? "";
  const vehicleId = vid ?? "";
  const navigate = useNavigate();
  const isOffline = useOnlineStatus();

  const vehicle = useVehicle(vehicleId);
  const updateVehicle = useUpdateVehicle(vehicleId, customerId);
  const archiveVehicle = useArchiveVehicle(customerId);
  const [archiveOpen, setArchiveOpen] = useState(false);

  if (vehicle.isPending) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Spinner />
      </div>
    );
  }

  const isNotFound = vehicle.error instanceof ApiError && vehicle.error.status === 404;
  if (isNotFound || !vehicle.data) {
    const errorCode = vehicle.error instanceof ApiError ? vehicle.error.code : "vehicle_not_found";
    return (
      <div className="flex flex-col gap-4">
        <Alert variant="error">{getCustomersErrorMessage(errorCode)}</Alert>
        <LinkButton to={`/clientes/${customerId}`} variant="secondary">
          {customersCopy.vehicles.edit.backToDetail}
        </LinkButton>
      </div>
    );
  }

  const data = vehicle.data;

  function handleSubmit(values: VehicleFormValues) {
    const payload = diffVehicle(data, values);
    updateVehicle.mutate(payload, {
      onSuccess: () => navigate(`/clientes/${customerId}/vehiculos/${vehicleId}`, { replace: true }),
    });
  }

  function handleArchiveConfirm() {
    archiveVehicle.mutate(vehicleId, {
      onSuccess: () => navigate(`/clientes/${customerId}`, { replace: true }),
    });
  }

  const errorMessage =
    updateVehicle.error instanceof ApiError ? getCustomersErrorMessage(updateVehicle.error.code) : undefined;

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-3xl font-bold text-brand-primary">{customersCopy.vehicles.edit.title}</h1>
      <VehicleForm
        mode="edit"
        initialValues={{
          vehicleType: data.vehicle_type,
          make: data.make,
          model: data.model ?? "",
          year: data.year !== null ? String(data.year) : "",
          color: data.color ?? "",
          plate: data.plate ?? "",
          notes: data.notes ?? "",
        }}
        onSubmit={handleSubmit}
        pending={updateVehicle.isPending}
        errorMessage={errorMessage}
        submitLabel={customersCopy.vehicles.edit.submit}
        submitPendingLabel={customersCopy.vehicles.edit.submitPending}
        offline={isOffline}
      />

      {isOffline ? <Alert variant="info">{customersCopy.vehicles.offline.archiveDisabled}</Alert> : null}

      <Button variant="destructive" onClick={() => setArchiveOpen(true)} disabled={isOffline}>
        {customersCopy.vehicles.edit.archiveAction}
      </Button>

      <Dialog
        open={archiveOpen}
        title={customersCopy.vehicles.edit.archiveConfirmTitle}
        onClose={() => setArchiveOpen(false)}
      >
        <div className="flex flex-col gap-4">
          <p className="text-base text-brand-foreground">{customersCopy.vehicles.edit.archiveConfirmBody}</p>
          {isOffline ? <Alert variant="info">{customersCopy.vehicles.offline.archiveDisabled}</Alert> : null}
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setArchiveOpen(false)}>
              {customersCopy.vehicles.edit.archiveConfirmCancel}
            </Button>
            <Button
              variant="destructive"
              onClick={handleArchiveConfirm}
              loading={archiveVehicle.isPending}
              disabled={isOffline || archiveVehicle.isPending}
            >
              {customersCopy.vehicles.edit.archiveConfirmSubmit}
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
