import { useMemo, useState } from "react";
import { useNavigate } from "react-router";

import { ApiError } from "../../shared/api/http";
import { useOnlineStatus } from "../../shared/offline/useOnlineStatus";
import { getInventoryErrorMessage, inventoryCopy } from "./copy";
import { useCreateItem, useItems } from "./hooks";
import { ItemForm, type ItemFormValues } from "./ItemForm";

/** Container: wires the shared item form to the create mutation and routing. */
export function NewItemPage() {
  const navigate = useNavigate();
  const isOffline = useOnlineStatus();
  const [itemId] = useState(() => crypto.randomUUID());
  const createItem = useCreateItem();
  const existingItems = useItems();

  const categorySuggestions = useMemo(() => {
    const categories = new Set<string>();
    for (const item of existingItems.data ?? []) {
      if (item.category) {
        categories.add(item.category);
      }
    }
    return [...categories].sort();
  }, [existingItems.data]);

  function handleSubmit(values: ItemFormValues) {
    createItem.mutate(
      {
        id: itemId,
        name: values.name,
        category: values.category || undefined,
        unit: values.unit,
        min_stock: values.minStock,
        sale_price_cents: values.priceCents ?? undefined,
        notes: values.notes || undefined,
        initial_stock: values.initialStock,
      },
      {
        onSuccess: (item) => navigate(`/inventario/${item.id}`, { replace: true }),
      },
    );
  }

  const errorMessage =
    createItem.error instanceof ApiError ? getInventoryErrorMessage(createItem.error.code) : undefined;

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-6 px-4 py-8">
      <h1 className="text-3xl font-bold text-brand-primary">{inventoryCopy.create.title}</h1>
      <ItemForm
        mode="create"
        categorySuggestions={categorySuggestions}
        onSubmit={handleSubmit}
        pending={createItem.isPending}
        errorMessage={errorMessage}
        submitLabel={inventoryCopy.create.submit}
        submitPendingLabel={inventoryCopy.create.submitPending}
        offline={isOffline}
      />
    </main>
  );
}
