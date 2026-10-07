import { useState } from "react";
import { useNavigate } from "react-router";

import { ApiError } from "../../shared/api/http";
import { useOnlineStatus } from "../../shared/offline/useOnlineStatus";
import { Alert } from "../../shared/ui/Alert";
import { Button } from "../../shared/ui/Button";
import { Spinner } from "../../shared/ui/Spinner";
import { TextField } from "../../shared/ui/TextField";
import { CustomerList } from "../customers/CustomerList";
import { useCustomers, useDebouncedValue, useVehiclesForCustomer } from "../customers/hooks";
import { VehicleList } from "../customers/VehicleList";
import { getWorkOrdersErrorMessage, workOrdersCopy } from "./copy";
import { useCreateWorkOrder } from "./hooks";
import type { CustomerOut, VehicleOut } from "../customers/api";

const SEARCH_DEBOUNCE_MS = 300;

type Step = "customer" | "vehicle" | "confirm";

/**
 * Container: customer search -> vehicle pick -> create, per `design.md`'s
 * `/ordenes/nueva` flow. The order's client id is generated once per form
 * mount, so a failed create and its retry (or a double tap of "Crear
 * orden") reuse the same id instead of burning a second number.
 */
export function NewWorkOrderPage() {
  const navigate = useNavigate();
  const isOffline = useOnlineStatus();
  const [orderId] = useState(() => crypto.randomUUID());
  const createOrder = useCreateWorkOrder();

  const [step, setStep] = useState<Step>("customer");
  const [customer, setCustomer] = useState<CustomerOut | null>(null);
  const [vehicle, setVehicle] = useState<VehicleOut | null>(null);

  const [searchInput, setSearchInput] = useState("");
  const debouncedQuery = useDebouncedValue(searchInput, SEARCH_DEBOUNCE_MS);
  const customers = useCustomers({ q: debouncedQuery.trim() || undefined });
  const vehicles = useVehiclesForCustomer(customer?.id ?? "");

  function handleSelectCustomer(selected: CustomerOut) {
    setCustomer(selected);
    setVehicle(null);
    setStep("vehicle");
  }

  function handleSelectVehicle(selected: VehicleOut) {
    setVehicle(selected);
    setStep("confirm");
  }

  function handleCreate() {
    if (!vehicle || isOffline) {
      return;
    }
    createOrder.mutate(
      { id: orderId, vehicle_id: vehicle.id },
      { onSuccess: (order) => navigate(`/ordenes/${order.id}`, { replace: true }) },
    );
  }

  const errorMessage =
    createOrder.error instanceof ApiError ? getWorkOrdersErrorMessage(createOrder.error.code) : undefined;

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold text-brand-primary">{workOrdersCopy.newOrder.title}</h1>

      {step === "customer" ? (
        <div className="flex flex-col gap-4">
          <TextField
            label={workOrdersCopy.newOrder.customerSearchLabel}
            placeholder={workOrdersCopy.newOrder.customerSearchPlaceholder}
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
          />
          {customers.isPending ? (
            <div className="flex justify-center py-8">
              <Spinner />
            </div>
          ) : (
            <CustomerList
              customers={customers.data ?? []}
              isFiltered={debouncedQuery.trim().length > 0}
              onOpen={handleSelectCustomer}
            />
          )}
        </div>
      ) : null}

      {step === "vehicle" && customer ? (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between gap-3">
            <p className="text-base font-semibold text-brand-foreground">{customer.full_name}</p>
            <Button variant="secondary" onClick={() => setStep("customer")} className="w-auto px-4">
              {workOrdersCopy.newOrder.changeCustomer}
            </Button>
          </div>
          {vehicles.isPending ? (
            <div className="flex justify-center py-8">
              <Spinner />
            </div>
          ) : (
            <VehicleList vehicles={vehicles.data ?? []} onOpen={handleSelectVehicle} />
          )}
        </div>
      ) : null}

      {step === "confirm" && customer && vehicle ? (
        <div className="flex flex-col gap-4">
          {errorMessage ? <Alert variant="error">{errorMessage}</Alert> : null}
          {isOffline ? <Alert variant="info">{workOrdersCopy.offline.createOrderDisabled}</Alert> : null}
          <div className="flex flex-col gap-1 rounded-2xl border border-brand-border bg-brand-card px-4 py-3">
            <p className="text-base font-semibold text-brand-foreground">{customer.full_name}</p>
            <p className="text-sm text-brand-muted-foreground">
              {[vehicle.make, vehicle.model].filter(Boolean).join(" ")}
              {vehicle.plate ? ` · ${vehicle.plate}` : ""}
            </p>
          </div>
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setStep("vehicle")}>
              {workOrdersCopy.newOrder.changeVehicle}
            </Button>
            <Button onClick={handleCreate} loading={createOrder.isPending} disabled={isOffline || createOrder.isPending}>
              {createOrder.isPending ? workOrdersCopy.newOrder.submitPending : workOrdersCopy.newOrder.submit}
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
