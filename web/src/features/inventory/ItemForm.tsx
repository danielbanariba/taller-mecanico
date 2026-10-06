import { useId, useState, type FormEvent } from "react";

import { Alert } from "../../shared/ui/Alert";
import { Button } from "../../shared/ui/Button";
import { TextArea } from "../../shared/ui/TextArea";
import { TextField } from "../../shared/ui/TextField";
import { inventoryCopy } from "./copy";
import { parseLempirasToCents } from "./format";

export interface ItemFormInitialValues {
  name: string;
  category: string;
  unit: string;
  minStock: number;
  priceText: string;
  notes: string;
  initialStock: number;
}

export interface ItemFormValues {
  name: string;
  category: string;
  unit: string;
  minStock: number;
  priceCents: number | null;
  notes: string;
  initialStock: number;
}

export interface ItemFormProps {
  mode: "create" | "edit";
  initialValues?: Partial<ItemFormInitialValues>;
  categorySuggestions: string[];
  onSubmit: (values: ItemFormValues) => void;
  pending: boolean;
  errorMessage?: string;
  submitLabel: string;
  submitPendingLabel: string;
}

/**
 * Presentational, shared by the create and edit screens. Owns every field's
 * value plus the two client-side checks worth enforcing before a round
 * trip: a required name and a well-formed price. Everything else (name
 * uniqueness) is the API's call. The caller decides what to do with the
 * resolved values (create sends them all; edit diffs against the current
 * item and PATCHes only what changed).
 */
export function ItemForm({
  mode,
  initialValues,
  categorySuggestions,
  onSubmit,
  pending,
  errorMessage,
  submitLabel,
  submitPendingLabel,
}: ItemFormProps) {
  const unitListId = useId();
  const categoryListId = useId();

  const [name, setName] = useState(initialValues?.name ?? "");
  const [category, setCategory] = useState(initialValues?.category ?? "");
  const [unit, setUnit] = useState(initialValues?.unit ?? inventoryCopy.units[0]);
  const [minStockText, setMinStockText] = useState(String(initialValues?.minStock ?? 0));
  const [priceText, setPriceText] = useState(initialValues?.priceText ?? "");
  const [notes, setNotes] = useState(initialValues?.notes ?? "");
  const [initialStockText, setInitialStockText] = useState(String(initialValues?.initialStock ?? 0));

  const [nameTouched, setNameTouched] = useState(false);
  const [priceTouched, setPriceTouched] = useState(false);

  const nameMissing = name.trim().length === 0;
  const parsedPrice = parseLempirasToCents(priceText);
  const priceInvalid = parsedPrice === undefined;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setNameTouched(true);
    setPriceTouched(true);
    if (nameMissing || priceInvalid) {
      return;
    }
    onSubmit({
      name: name.trim(),
      category: category.trim(),
      unit: unit.trim() || inventoryCopy.units[0],
      minStock: Math.max(0, Math.trunc(Number(minStockText) || 0)),
      priceCents: parsedPrice ?? null,
      notes: notes.trim(),
      initialStock: Math.max(0, Math.trunc(Number(initialStockText) || 0)),
    });
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      {errorMessage ? <Alert variant="error">{errorMessage}</Alert> : null}
      <TextField
        label={inventoryCopy.create.nameLabel}
        name="name"
        value={name}
        onChange={(event) => setName(event.target.value)}
        onBlur={() => setNameTouched(true)}
        error={nameTouched && nameMissing ? inventoryCopy.create.nameRequired : undefined}
        required
      />
      {mode === "create" ? (
        <TextField
          label={inventoryCopy.create.initialStockLabel}
          name="initial_stock"
          type="number"
          inputMode="numeric"
          min={0}
          value={initialStockText}
          onChange={(event) => setInitialStockText(event.target.value)}
        />
      ) : null}
      <div className="flex flex-col gap-1.5">
        <label htmlFor={unitListId} className="text-base font-medium text-brand-foreground">
          {inventoryCopy.create.unitLabel}
        </label>
        <input
          id={unitListId}
          name="unit"
          list={`${unitListId}-options`}
          value={unit}
          onChange={(event) => setUnit(event.target.value)}
          className="min-h-12 rounded-xl border border-brand-border px-4 text-base text-brand-foreground outline-none focus:ring-2 focus:ring-brand-accent"
        />
        <datalist id={`${unitListId}-options`}>
          {inventoryCopy.units.map((option) => (
            <option key={option} value={option} />
          ))}
        </datalist>
      </div>
      <div className="flex flex-col gap-1.5">
        <label htmlFor={categoryListId} className="text-base font-medium text-brand-foreground">
          {inventoryCopy.create.categoryLabel}
        </label>
        <input
          id={categoryListId}
          name="category"
          list={`${categoryListId}-options`}
          value={category}
          onChange={(event) => setCategory(event.target.value)}
          className="min-h-12 rounded-xl border border-brand-border px-4 text-base text-brand-foreground outline-none focus:ring-2 focus:ring-brand-accent"
        />
        <datalist id={`${categoryListId}-options`}>
          {categorySuggestions.map((option) => (
            <option key={option} value={option} />
          ))}
        </datalist>
      </div>
      <TextField
        label={inventoryCopy.create.minStockLabel}
        name="min_stock"
        type="number"
        inputMode="numeric"
        min={0}
        helperText={inventoryCopy.create.minStockHelper}
        value={minStockText}
        onChange={(event) => setMinStockText(event.target.value)}
      />
      <TextField
        label={inventoryCopy.create.priceLabel}
        name="sale_price"
        inputMode="decimal"
        placeholder={inventoryCopy.create.pricePlaceholder}
        value={priceText}
        onChange={(event) => setPriceText(event.target.value)}
        onBlur={() => setPriceTouched(true)}
        error={priceTouched && priceInvalid ? inventoryCopy.create.priceInvalid : undefined}
      />
      <TextArea
        label={inventoryCopy.create.notesLabel}
        name="notes"
        value={notes}
        onChange={(event) => setNotes(event.target.value)}
      />
      <Button type="submit" loading={pending} disabled={pending}>
        {pending ? submitPendingLabel : submitLabel}
      </Button>
    </form>
  );
}
