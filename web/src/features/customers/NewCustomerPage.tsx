import { useState } from "react";
import { useNavigate } from "react-router";

import { ApiError } from "../../shared/api/http";
import { useOnlineStatus } from "../../shared/offline/useOnlineStatus";
import { CustomerForm, type CustomerFormValues } from "./CustomerForm";
import { customersCopy, getCustomersErrorMessage } from "./copy";
import { useCreateCustomer } from "./hooks";

/** Container: wires the shared customer form to the create mutation and routing. */
export function NewCustomerPage() {
  const navigate = useNavigate();
  const isOffline = useOnlineStatus();
  const [customerId] = useState(() => crypto.randomUUID());
  const createCustomer = useCreateCustomer();

  function handleSubmit(values: CustomerFormValues) {
    createCustomer.mutate(
      {
        id: customerId,
        full_name: values.fullName,
        phone: values.phone || undefined,
        notes: values.notes || undefined,
      },
      {
        onSuccess: () => navigate("/clientes", { replace: true }),
      },
    );
  }

  const errorMessage =
    createCustomer.error instanceof ApiError ? getCustomersErrorMessage(createCustomer.error.code) : undefined;

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-6 px-4 py-8">
      <h1 className="text-3xl font-bold text-brand-primary">{customersCopy.create.title}</h1>
      <CustomerForm
        mode="create"
        onSubmit={handleSubmit}
        pending={createCustomer.isPending}
        errorMessage={errorMessage}
        submitLabel={customersCopy.create.submit}
        submitPendingLabel={customersCopy.create.submitPending}
        offline={isOffline}
      />
    </main>
  );
}
