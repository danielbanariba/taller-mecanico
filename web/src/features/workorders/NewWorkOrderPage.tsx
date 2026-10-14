import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router";

import { ApiError } from "../../shared/api/http";
import { useOnlineStatus } from "../../shared/offline/useOnlineStatus";
import { Alert } from "../../shared/ui/Alert";
import { Button } from "../../shared/ui/Button";
import { Spinner } from "../../shared/ui/Spinner";
import { TextField } from "../../shared/ui/TextField";
import { CustomerForm, type CustomerFormValues } from "../customers/CustomerForm";
import { CustomerList } from "../customers/CustomerList";
import { customersCopy, getCustomersErrorMessage } from "../customers/copy";
import {
  buildCreateCustomerPayload,
  buildCreateVehiclePayload,
  useCreateCustomer,
  useCreateVehicle,
  useCustomers,
  useDebouncedValue,
  useVehicle,
  useVehiclesForCustomer,
} from "../customers/hooks";
import { VehicleForm, type VehicleFormValues } from "../customers/VehicleForm";
import { VehicleList } from "../customers/VehicleList";
import { getWorkOrdersErrorMessage, workOrdersCopy } from "./copy";
import { useCreateWorkOrder } from "./hooks";
import type { CustomerOut, VehicleOut } from "../customers/api";

const SEARCH_DEBOUNCE_MS = 300;

type Step = "customer" | "vehicle" | "confirm";

/**
 * Container: customer search -> vehicle pick -> create, per `design.md`'s
 * `/ordenes/nueva` flow. A `?vehiculo=<id>` query param -- set by the
 * vehicle detail screen's "Nueva orden" action -- skips both picker steps
 * straight to the confirm step for that vehicle and its owner; if that
 * vehicle fails to load (a stale link), this falls back to the normal
 * picker instead of leaving the screen stuck with no vehicle and no way
 * forward. The order's client id is generated once per form mount, so a
 * failed create and its retry (or a double tap of "Crear orden") reuse the
 * same id instead of burning a second number.
 *
 * Both picker steps can also create the record inline (a walk-in customer,
 * or a customer's first vehicle) instead of forcing a detour to the
 * Clientes screens: the inline forms reuse `CustomerForm`/`VehicleForm` and
 * their existing create mutations unchanged, so the id-replay guarantee,
 * the offline disablement and the query invalidation above all carry over
 * for free.
 */
export function NewWorkOrderPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const preselectedVehicleId = searchParams.get("vehiculo") ?? "";
  const isOffline = useOnlineStatus();
  const [orderId] = useState(() => crypto.randomUUID());
  const createOrder = useCreateWorkOrder();
  const preselectedVehicle = useVehicle(preselectedVehicleId);

  const [step, setStep] = useState<Step>("customer");
  const [customer, setCustomer] = useState<CustomerOut | null>(null);
  const [vehicle, setVehicle] = useState<VehicleOut | null>(null);

  const [searchInput, setSearchInput] = useState("");
  const debouncedQuery = useDebouncedValue(searchInput, SEARCH_DEBOUNCE_MS);
  const customers = useCustomers({ q: debouncedQuery.trim() || undefined });
  const vehicles = useVehiclesForCustomer(customer?.id ?? "");

  const [showNewCustomerForm, setShowNewCustomerForm] = useState(false);
  const [showNewVehicleForm, setShowNewVehicleForm] = useState(false);
  // Regenerated on every open (below), not just once per mount: the
  // customer/vehicle step can be revisited ("Cambiar cliente"/"Cambiar
  // vehículo") and the inline form reopened to create a second, different
  // record in the same page session, which must never reuse the id of the
  // first create -- the API treats a reused id with different fields as a
  // conflict (VehicleIdConflict/CustomerIdConflict), not a replay.
  const [newCustomerId, setNewCustomerId] = useState(() => crypto.randomUUID());
  const [newVehicleId, setNewVehicleId] = useState(() => crypto.randomUUID());
  const createCustomer = useCreateCustomer();
  const createVehicle = useCreateVehicle(customer?.id ?? "");

  function handleOpenNewCustomerForm() {
    setNewCustomerId(crypto.randomUUID());
    setShowNewCustomerForm(true);
  }

  function handleOpenNewVehicleForm() {
    setNewVehicleId(crypto.randomUUID());
    setShowNewVehicleForm(true);
  }

  // Only trusted once resolved: an id that fails to load (404, or another
  // workshop's) falls through to `hasPreselection === false` below, instead
  // of forcing `effectiveStep` to "confirm" with nothing to confirm.
  const hasPreselection =
    preselectedVehicleId !== "" && (preselectedVehicle.isPending || preselectedVehicle.data !== undefined);

  function handleSelectCustomer(selected: CustomerOut) {
    setCustomer(selected);
    setVehicle(null);
    setShowNewVehicleForm(false);
    setStep("vehicle");
  }

  function handleSelectVehicle(selected: VehicleOut) {
    setVehicle(selected);
    setStep("confirm");
  }

  function handleCreateCustomerSubmit(values: CustomerFormValues) {
    createCustomer.mutate(buildCreateCustomerPayload(newCustomerId, values), {
      onSuccess: (created) => {
        setShowNewCustomerForm(false);
        handleSelectCustomer(created);
      },
    });
  }

  function handleCreateVehicleSubmit(values: VehicleFormValues) {
    if (!customer) {
      return;
    }
    createVehicle.mutate(buildCreateVehiclePayload(newVehicleId, customer.id, values), {
      onSuccess: (created) => {
        setShowNewVehicleForm(false);
        handleSelectVehicle(created);
      },
    });
  }

  const effectiveVehicle = hasPreselection ? preselectedVehicle.data ?? null : vehicle;
  const effectiveCustomer = hasPreselection ? preselectedVehicle.data?.owner ?? null : customer;
  const effectiveStep: Step = hasPreselection ? "confirm" : step;

  function handleCreate() {
    if (!effectiveVehicle || isOffline) {
      return;
    }
    createOrder.mutate(
      { id: orderId, vehicle_id: effectiveVehicle.id },
      { onSuccess: (order) => navigate(`/ordenes/${order.id}`, { replace: true }) },
    );
  }

  const errorMessage =
    createOrder.error instanceof ApiError ? getWorkOrdersErrorMessage(createOrder.error.code) : undefined;
  const createCustomerErrorMessage =
    createCustomer.error instanceof ApiError ? getCustomersErrorMessage(createCustomer.error.code) : undefined;
  const createVehicleErrorMessage =
    createVehicle.error instanceof ApiError ? getCustomersErrorMessage(createVehicle.error.code) : undefined;

  // True when there is nothing cached to show AND the reason is connectivity
  // (either the browser already knows it is offline, or the very first
  // fetch already settled into a `network_error`). A cold load that starts
  // offline resolves `customers.isPending`/`vehicles.isPending` to `false`
  // almost immediately -- the query settles into its error state -- so
  // branching on `isPending` alone (as this used to) fell through to
  // `CustomerList`/`VehicleList`'s own empty state ("Todavía no hay
  // clientes/vehículos"), which reads as "this workshop has none" instead
  // of "you're offline" (a QA sweep finding). Cached data (`data !==
  // undefined`) always wins over this, so a normal offline read with
  // something already cached keeps showing it.
  const customersUnavailable =
    customers.data === undefined &&
    (isOffline || (customers.error instanceof ApiError && customers.error.code === "network_error"));
  const vehiclesUnavailable =
    vehicles.data === undefined &&
    (isOffline || (vehicles.error instanceof ApiError && vehicles.error.code === "network_error"));

  if (preselectedVehicleId !== "" && preselectedVehicle.isPending) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold text-brand-primary">{workOrdersCopy.newOrder.title}</h1>

      {effectiveStep === "customer" ? (
        <div className="flex flex-col gap-4">
          {showNewCustomerForm ? (
            <div className="flex flex-col gap-4">
              <div className="flex items-center justify-between gap-3">
                <p className="text-base font-semibold text-brand-foreground">{customersCopy.create.title}</p>
                <Button
                  variant="secondary"
                  fullWidth={false}
                  className="px-4"
                  onClick={() => setShowNewCustomerForm(false)}
                >
                  {workOrdersCopy.newOrder.cancelCreate}
                </Button>
              </div>
              <CustomerForm
                mode="create"
                onSubmit={handleCreateCustomerSubmit}
                pending={createCustomer.isPending}
                errorMessage={createCustomerErrorMessage}
                submitLabel={customersCopy.create.submit}
                submitPendingLabel={customersCopy.create.submitPending}
                offline={isOffline}
              />
            </div>
          ) : (
            <>
              <TextField
                label={workOrdersCopy.newOrder.customerSearchLabel}
                placeholder={workOrdersCopy.newOrder.customerSearchPlaceholder}
                value={searchInput}
                onChange={(event) => setSearchInput(event.target.value)}
              />
              {customersUnavailable ? (
                <Alert variant="info">{workOrdersCopy.offline.customerSearchDisabled}</Alert>
              ) : customers.isPending ? (
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
              <Button variant="secondary" onClick={handleOpenNewCustomerForm}>
                {workOrdersCopy.newOrder.newCustomer}
              </Button>
            </>
          )}
        </div>
      ) : null}

      {effectiveStep === "vehicle" && effectiveCustomer ? (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between gap-3">
            <p className="text-base font-semibold text-brand-foreground">{effectiveCustomer.full_name}</p>
            <Button variant="secondary" onClick={() => setStep("customer")} fullWidth={false} className="px-4">
              {workOrdersCopy.newOrder.changeCustomer}
            </Button>
          </div>
          {showNewVehicleForm ? (
            <div className="flex flex-col gap-4">
              <div className="flex items-center justify-between gap-3">
                <p className="text-base font-semibold text-brand-foreground">
                  {customersCopy.vehicles.create.title}
                </p>
                <Button
                  variant="secondary"
                  fullWidth={false}
                  className="px-4"
                  onClick={() => setShowNewVehicleForm(false)}
                >
                  {workOrdersCopy.newOrder.cancelCreate}
                </Button>
              </div>
              <VehicleForm
                mode="create"
                onSubmit={handleCreateVehicleSubmit}
                pending={createVehicle.isPending}
                errorMessage={createVehicleErrorMessage}
                submitLabel={customersCopy.vehicles.create.submit}
                submitPendingLabel={customersCopy.vehicles.create.submitPending}
                offline={isOffline}
              />
            </div>
          ) : (
            <>
              {vehiclesUnavailable ? (
                <Alert variant="info">{workOrdersCopy.offline.vehicleListDisabled}</Alert>
              ) : vehicles.isPending ? (
                <div className="flex justify-center py-8">
                  <Spinner />
                </div>
              ) : (
                <VehicleList vehicles={vehicles.data ?? []} onOpen={handleSelectVehicle} />
              )}
              <Button variant="secondary" onClick={handleOpenNewVehicleForm}>
                {workOrdersCopy.newOrder.newVehicle}
              </Button>
            </>
          )}
        </div>
      ) : null}

      {effectiveStep === "confirm" && effectiveCustomer && effectiveVehicle ? (
        <div className="flex flex-col gap-4">
          {errorMessage ? <Alert variant="error">{errorMessage}</Alert> : null}
          {isOffline ? <Alert variant="info">{workOrdersCopy.offline.createOrderDisabled}</Alert> : null}
          <div className="flex flex-col gap-1 rounded-2xl border border-brand-border bg-brand-card px-4 py-3">
            <p className="text-base font-semibold text-brand-foreground">{effectiveCustomer.full_name}</p>
            <p className="text-sm text-brand-muted-foreground">
              {[effectiveVehicle.make, effectiveVehicle.model].filter(Boolean).join(" ")}
              {effectiveVehicle.plate ? ` · ${effectiveVehicle.plate}` : ""}
            </p>
          </div>
          <div className="flex gap-3">
            {hasPreselection ? null : (
              <Button variant="secondary" onClick={() => setStep("vehicle")}>
                {workOrdersCopy.newOrder.changeVehicle}
              </Button>
            )}
            <Button onClick={handleCreate} loading={createOrder.isPending} disabled={isOffline || createOrder.isPending}>
              {createOrder.isPending ? workOrdersCopy.newOrder.submitPending : workOrdersCopy.newOrder.submit}
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
