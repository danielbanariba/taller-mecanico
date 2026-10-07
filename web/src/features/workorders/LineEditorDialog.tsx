import { useState } from "react";

import { centsToPlainAmount, formatCents, parseLempirasToCents } from "../../shared/format/money";
import { Alert } from "../../shared/ui/Alert";
import { Button } from "../../shared/ui/Button";
import { Chip } from "../../shared/ui/Chip";
import { Dialog } from "../../shared/ui/Dialog";
import { TextField } from "../../shared/ui/TextField";
import { ItemPicker } from "./ItemPicker";
import { lineKindLabel, workOrdersCopy } from "./copy";
import type { ItemOut } from "../inventory/api";
import type { LineKind, WorkOrderLineOut } from "./api";

const MIN_QUANTITY = 1;
const MAX_QUANTITY = 10_000;
const MAX_PRICE_CENTS = 1_000_000_000;
const MAX_DESCRIPTION_LENGTH = 200;

const KIND_OPTIONS: LineKind[] = ["labor", "inventory_part", "external_part"];

/** Parses a positive integer quantity typed by the user; `undefined` for anything else (matches the API's own `WorkOrderLineCreateRequest` shape, not inventory's stock-quantity bounds). */
function parseQuantity(text: string): number | undefined {
  const trimmed = text.trim();
  if (!/^\d+$/.test(trimmed)) {
    return undefined;
  }
  return Number(trimmed);
}

export interface LineEditorValues {
  kind: LineKind;
  itemId?: string;
  description: string;
  quantity: number;
  unitPriceCents: number;
}

export interface LineEditorDialogProps {
  open: boolean;
  mode: "create" | "edit";
  /** Required in edit mode: the line being edited (`kind`/`item_id` are immutable, per the `work-orders` spec). */
  initialLine?: WorkOrderLineOut;
  pending: boolean;
  errorMessage?: string;
  offline: boolean;
  onClose: () => void;
  onSubmit: (values: LineEditorValues) => void;
}

/**
 * Adds or edits one work-order quote line. In create mode, an
 * inventory-part line requires picking an item first (`ItemPicker`); kind
 * and item are immutable once a line exists, so edit mode only changes
 * description/quantity/price. Every field below is local component state
 * and plain arithmetic -- no query mutation runs until the mechanic taps
 * "Guardar línea", so the subtotal preview never touches inventory stock
 * ahead of the server's own response.
 *
 * Every field initializes once from `initialLine` and never reacts to a
 * later prop change (no reset effect: this app's lint config forbids
 * calling `setState` from an effect body). The caller must remount this
 * component with a fresh `key` (e.g. the target line's id, or a constant
 * for "new line") whenever it should start over for a different line or
 * mode -- see `WorkOrderDetailPage.tsx`.
 */
export function LineEditorDialog({
  open,
  mode,
  initialLine,
  pending,
  errorMessage,
  offline,
  onClose,
  onSubmit,
}: LineEditorDialogProps) {
  const [kind, setKind] = useState<LineKind>(initialLine?.kind ?? "labor");
  const [pickingItem, setPickingItem] = useState(false);
  const [selectedItem, setSelectedItem] = useState<ItemOut | null>(null);
  const [description, setDescription] = useState(initialLine?.description ?? "");
  const [quantityText, setQuantityText] = useState(String(initialLine?.quantity ?? 1));
  const [priceText, setPriceText] = useState(initialLine ? centsToPlainAmount(initialLine.unit_price_cents) : "");
  const [touched, setTouched] = useState(false);

  const trimmedDescription = description.trim();
  const descriptionInvalid = trimmedDescription.length === 0 || trimmedDescription.length > MAX_DESCRIPTION_LENGTH;

  const parsedQuantity = parseQuantity(quantityText);
  const quantityInvalid =
    parsedQuantity === undefined || parsedQuantity < MIN_QUANTITY || parsedQuantity > MAX_QUANTITY;

  const parsedPrice = parseLempirasToCents(priceText);
  const priceInvalid = typeof parsedPrice !== "number" || parsedPrice > MAX_PRICE_CENTS;

  const itemMissing = mode === "create" && kind === "inventory_part" && selectedItem === null;

  const subtotalCents =
    !quantityInvalid && !priceInvalid && typeof parsedPrice === "number" && parsedQuantity !== undefined
      ? parsedQuantity * parsedPrice
      : null;

  function handleKindChange(nextKind: LineKind) {
    setKind(nextKind);
    setSelectedItem(null);
    setPickingItem(false);
  }

  function handleSelectItem(item: ItemOut) {
    setSelectedItem(item);
    setPickingItem(false);
    setDescription((current) => (current.trim().length > 0 ? current : item.name));
    if (item.sale_price_cents != null && priceText.trim().length === 0) {
      setPriceText(centsToPlainAmount(item.sale_price_cents));
    }
  }

  function handleSubmit() {
    setTouched(true);
    if (offline || descriptionInvalid || quantityInvalid || priceInvalid || itemMissing) {
      return;
    }
    onSubmit({
      kind,
      itemId: mode === "edit" ? (initialLine?.item_id ?? undefined) : (selectedItem?.id ?? undefined),
      description: trimmedDescription,
      quantity: parsedQuantity as number,
      unitPriceCents: parsedPrice as number,
    });
  }

  const title = mode === "edit" ? workOrdersCopy.lineEditor.editLineTitle : workOrdersCopy.lineEditor.addLineTitle;

  return (
    <Dialog open={open} title={title} onClose={onClose}>
      {pickingItem ? (
        <div className="flex flex-col gap-3">
          <ItemPicker onSelect={handleSelectItem} />
          <Button variant="secondary" onClick={() => setPickingItem(false)}>
            {workOrdersCopy.itemPicker.back}
          </Button>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {errorMessage ? <Alert variant="error">{errorMessage}</Alert> : null}
          {offline ? <Alert variant="info">{workOrdersCopy.offline.lineEditDisabled}</Alert> : null}

          {mode === "create" ? (
            <div className="flex flex-col gap-1.5">
              <span className="text-base font-medium text-brand-foreground">{workOrdersCopy.lineEditor.kindLabel}</span>
              <div className="flex flex-wrap gap-2">
                {KIND_OPTIONS.map((option) => (
                  <Chip key={option} active={kind === option} onClick={() => handleKindChange(option)}>
                    {lineKindLabel(option)}
                  </Chip>
                ))}
              </div>
            </div>
          ) : null}

          {mode === "create" && kind === "inventory_part" ? (
            <div className="flex flex-col gap-2">
              <span className="text-base font-medium text-brand-foreground">{workOrdersCopy.lineEditor.itemLabel}</span>
              {selectedItem ? (
                <div className="flex items-center justify-between gap-2">
                  <span className="text-base text-brand-foreground">{selectedItem.name}</span>
                  <Button variant="secondary" onClick={() => setPickingItem(true)} className="w-auto px-4">
                    {workOrdersCopy.itemPicker.changeItem}
                  </Button>
                </div>
              ) : (
                <>
                  <Button variant="secondary" onClick={() => setPickingItem(true)}>
                    {workOrdersCopy.lineEditor.pickItem}
                  </Button>
                  {touched && itemMissing ? (
                    <p role="alert" className="text-sm font-medium text-brand-destructive">
                      {workOrdersCopy.lineEditor.itemRequired}
                    </p>
                  ) : null}
                </>
              )}
            </div>
          ) : null}

          <TextField
            label={workOrdersCopy.lineEditor.descriptionLabel}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            maxLength={MAX_DESCRIPTION_LENGTH + 1}
            error={touched && descriptionInvalid ? workOrdersCopy.lineEditor.descriptionRequired : undefined}
          />
          <TextField
            label={workOrdersCopy.lineEditor.quantityLabel}
            type="number"
            inputMode="numeric"
            min={MIN_QUANTITY}
            max={MAX_QUANTITY}
            value={quantityText}
            onChange={(event) => setQuantityText(event.target.value)}
            error={touched && quantityInvalid ? workOrdersCopy.lineEditor.quantityInvalid : undefined}
          />
          <TextField
            label={workOrdersCopy.lineEditor.priceLabel}
            inputMode="decimal"
            value={priceText}
            onChange={(event) => setPriceText(event.target.value)}
            error={touched && priceInvalid ? workOrdersCopy.lineEditor.priceInvalid : undefined}
          />
          <p className="flex items-center justify-between text-base font-semibold text-brand-foreground">
            <span>{workOrdersCopy.lineEditor.subtotalLabel}</span>
            <span>{subtotalCents !== null ? formatCents(subtotalCents) : "—"}</span>
          </p>

          <div className="flex gap-3">
            <Button variant="secondary" onClick={onClose}>
              {workOrdersCopy.lineEditor.cancel}
            </Button>
            <Button onClick={handleSubmit} loading={pending} disabled={pending || offline}>
              {pending ? workOrdersCopy.lineEditor.savePending : workOrdersCopy.lineEditor.save}
            </Button>
          </div>
        </div>
      )}
    </Dialog>
  );
}
