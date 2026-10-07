import { useMemo } from "react";
import { useNavigate, useParams } from "react-router";

import { ApiError } from "../../shared/api/http";
import { useOnlineStatus } from "../../shared/offline/useOnlineStatus";
import { Alert } from "../../shared/ui/Alert";
import { LinkButton } from "../../shared/ui/LinkButton";
import { Spinner } from "../../shared/ui/Spinner";
import { getInventoryErrorMessage, inventoryCopy } from "./copy";
import { centsToPlainAmount } from "./format";
import { useItem, useItems, useUpdateItem } from "./hooks";
import { ItemForm, type ItemFormValues } from "./ItemForm";
import type { ItemOut, UpdateItemPayload } from "./api";

/** Computes the minimal PATCH payload: only the fields the form actually changed. */
function diffItem(item: ItemOut, values: ItemFormValues): UpdateItemPayload {
  const payload: UpdateItemPayload = {};

  if (values.name !== item.name) {
    payload.name = values.name;
  }
  const originalCategory = item.category ?? "";
  if (values.category !== originalCategory) {
    payload.category = values.category === "" ? null : values.category;
  }
  if (values.unit !== item.unit) {
    payload.unit = values.unit;
  }
  if (values.minStock !== item.min_stock) {
    payload.min_stock = values.minStock;
  }
  const originalPriceCents = item.sale_price_cents ?? null;
  if (values.priceCents !== originalPriceCents) {
    payload.sale_price_cents = values.priceCents;
  }
  const originalNotes = item.notes ?? "";
  if (values.notes !== originalNotes) {
    payload.notes = values.notes === "" ? null : values.notes;
  }

  return payload;
}

/** Container: wires the shared item form to the update mutation, sending only changed fields. */
export function EditItemPage() {
  const { id } = useParams<{ id: string }>();
  const itemId = id ?? "";
  const navigate = useNavigate();
  const isOffline = useOnlineStatus();

  const item = useItem(itemId);
  const existingItems = useItems();
  const updateItem = useUpdateItem(itemId);

  const categorySuggestions = useMemo(() => {
    const categories = new Set<string>();
    for (const existing of existingItems.data ?? []) {
      if (existing.category) {
        categories.add(existing.category);
      }
    }
    return [...categories].sort();
  }, [existingItems.data]);

  if (item.isPending) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Spinner />
      </div>
    );
  }

  // Same rule as the detail page: a failed refetch keeps the cached item;
  // only the server saying the item is gone replaces it.
  const isNotFound = item.error instanceof ApiError && item.error.status === 404;
  if (isNotFound || !item.data) {
    const errorCode = item.error instanceof ApiError ? item.error.code : "item_not_found";
    return (
      <div className="flex flex-col gap-4">
        <Alert variant="error">{getInventoryErrorMessage(errorCode)}</Alert>
        <LinkButton to="/inventario" variant="secondary">
          {inventoryCopy.detail.backToList}
        </LinkButton>
      </div>
    );
  }

  const data = item.data;

  function handleSubmit(values: ItemFormValues) {
    const payload = diffItem(data, values);
    updateItem.mutate(payload, {
      onSuccess: () => navigate(`/inventario/${itemId}`, { replace: true }),
    });
  }

  const errorMessage =
    updateItem.error instanceof ApiError ? getInventoryErrorMessage(updateItem.error.code) : undefined;

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-3xl font-bold text-brand-primary">{inventoryCopy.edit.title}</h1>
      <ItemForm
        mode="edit"
        initialValues={{
          name: data.name,
          category: data.category ?? "",
          unit: data.unit,
          minStock: data.min_stock,
          priceText: data.sale_price_cents != null ? centsToPlainAmount(data.sale_price_cents) : "",
          notes: data.notes ?? "",
        }}
        categorySuggestions={categorySuggestions}
        onSubmit={handleSubmit}
        pending={updateItem.isPending}
        errorMessage={errorMessage}
        submitLabel={inventoryCopy.edit.submit}
        submitPendingLabel={inventoryCopy.edit.submitPending}
        offline={isOffline}
      />
    </div>
  );
}
