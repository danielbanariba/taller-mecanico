import { useState } from "react";
import { useNavigate, useParams } from "react-router";

import { ApiError } from "../../shared/api/http";
import { useOnlineStatus } from "../../shared/offline/useOnlineStatus";
import { Alert } from "../../shared/ui/Alert";
import { Button } from "../../shared/ui/Button";
import { Dialog } from "../../shared/ui/Dialog";
import { LinkButton } from "../../shared/ui/LinkButton";
import { Spinner } from "../../shared/ui/Spinner";
import { CustomerForm, type CustomerFormValues } from "./CustomerForm";
import { customersCopy, getCustomersErrorMessage } from "./copy";
import { useArchiveCustomer, useCustomer, useUpdateCustomer } from "./hooks";
import type { CustomerOut, UpdateCustomerPayload } from "./api";

/** Computes the minimal PATCH payload: only the fields the form actually changed. */
function diffCustomer(customer: CustomerOut, values: CustomerFormValues): UpdateCustomerPayload {
  const payload: UpdateCustomerPayload = {};

  if (values.fullName !== customer.full_name) {
    payload.full_name = values.fullName;
  }
  const originalPhone = customer.phone ?? "";
  if (values.phone !== originalPhone) {
    payload.phone = values.phone === "" ? null : values.phone;
  }
  const originalNotes = customer.notes ?? "";
  if (values.notes !== originalNotes) {
    payload.notes = values.notes === "" ? null : values.notes;
  }

  return payload;
}

/** Container: wires the shared customer form to the update mutation, and owns archiving. */
export function EditCustomerPage() {
  const { customerId: id } = useParams<{ customerId: string }>();
  const customerId = id ?? "";
  const navigate = useNavigate();
  const isOffline = useOnlineStatus();

  const customer = useCustomer(customerId);
  const updateCustomer = useUpdateCustomer(customerId);
  const archiveCustomer = useArchiveCustomer();
  const [archiveOpen, setArchiveOpen] = useState(false);

  if (customer.isPending) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Spinner />
      </div>
    );
  }

  // A failed refetch keeps the cached customer; only the server saying the
  // customer is gone replaces it (same rule inventory's item pages use).
  const isNotFound = customer.error instanceof ApiError && customer.error.status === 404;
  if (isNotFound || !customer.data) {
    const errorCode = customer.error instanceof ApiError ? customer.error.code : "customer_not_found";
    return (
      <div className="flex flex-col gap-4">
        <Alert variant="error">{getCustomersErrorMessage(errorCode)}</Alert>
        <LinkButton to="/clientes" variant="secondary">
          {customersCopy.edit.backToList}
        </LinkButton>
      </div>
    );
  }

  const data = customer.data;

  function handleSubmit(values: CustomerFormValues) {
    const payload = diffCustomer(data, values);
    updateCustomer.mutate(payload, {
      onSuccess: () => navigate("/clientes", { replace: true }),
    });
  }

  function handleArchiveConfirm() {
    archiveCustomer.mutate(customerId, {
      onSuccess: () => navigate("/clientes", { replace: true }),
    });
  }

  const errorMessage =
    updateCustomer.error instanceof ApiError ? getCustomersErrorMessage(updateCustomer.error.code) : undefined;

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-3xl font-bold text-brand-primary">{customersCopy.edit.title}</h1>
      <CustomerForm
        mode="edit"
        initialValues={{ fullName: data.full_name, phone: data.phone ?? "", notes: data.notes ?? "" }}
        onSubmit={handleSubmit}
        pending={updateCustomer.isPending}
        errorMessage={errorMessage}
        submitLabel={customersCopy.edit.submit}
        submitPendingLabel={customersCopy.edit.submitPending}
        offline={isOffline}
      />

      {isOffline ? <Alert variant="info">{customersCopy.offline.archiveDisabled}</Alert> : null}

      <Button variant="destructive" onClick={() => setArchiveOpen(true)} disabled={isOffline}>
        {customersCopy.edit.archiveAction}
      </Button>

      <Dialog open={archiveOpen} title={customersCopy.edit.archiveConfirmTitle} onClose={() => setArchiveOpen(false)}>
        <div className="flex flex-col gap-4">
          <p className="text-base text-brand-foreground">{customersCopy.edit.archiveConfirmBody}</p>
          {isOffline ? <Alert variant="info">{customersCopy.offline.archiveDisabled}</Alert> : null}
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setArchiveOpen(false)}>
              {customersCopy.edit.archiveConfirmCancel}
            </Button>
            <Button
              variant="destructive"
              onClick={handleArchiveConfirm}
              loading={archiveCustomer.isPending}
              disabled={isOffline || archiveCustomer.isPending}
            >
              {customersCopy.edit.archiveConfirmSubmit}
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
