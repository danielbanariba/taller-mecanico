import { inventoryApi, type ItemOut, type MovementKind, type MovementResult } from "./api";

export interface RecordMovementInput {
  itemId: string;
  kind: MovementKind;
  quantity: number;
  note?: string;
}

/**
 * The single place every stock change goes through, for the list, the
 * detail stepper and the physical count dialog alike. It generates the
 * movement's id and `occurred_at` on the client so a retried or replayed
 * call is idempotent (see the T3 ledger). T6 redirects this through an
 * offline outbox instead of calling `inventoryApi.putMovement` directly;
 * no hook or screen above this module needs to change for that.
 */
export function recordMovement(input: RecordMovementInput): Promise<MovementResult> {
  const movementId = crypto.randomUUID();
  const occurredAt = new Date().toISOString();
  return inventoryApi.putMovement(movementId, {
    item_id: input.itemId,
    kind: input.kind,
    quantity: input.quantity,
    note: input.note,
    occurred_at: occurredAt,
  });
}

/**
 * Applies a movement to an item's cached stock fields optimistically, with
 * the same rules the API uses: `in`/`out` move the stock by `quantity`, an
 * `adjust` replaces it with the counted `quantity`; `needs_review` and
 * `is_low` are re-derived from the resulting stock.
 */
export function applyMovementToItem(
  item: ItemOut,
  input: Pick<RecordMovementInput, "kind" | "quantity">,
): ItemOut {
  const stock =
    input.kind === "adjust"
      ? input.quantity
      : item.stock + (input.kind === "in" ? input.quantity : -input.quantity);

  return {
    ...item,
    stock,
    needs_review: stock < 0,
    is_low: item.min_stock > 0 && stock <= item.min_stock,
  };
}
