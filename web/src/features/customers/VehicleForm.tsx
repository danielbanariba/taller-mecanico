import { useState, type FormEvent } from "react";

import { Alert } from "../../shared/ui/Alert";
import { Button } from "../../shared/ui/Button";
import { TextArea } from "../../shared/ui/TextArea";
import { TextField } from "../../shared/ui/TextField";
import { customersCopy } from "./copy";
import type { VehicleType } from "./api";

const MAX_MAKE_LENGTH = 60;
const MAX_MODEL_LENGTH = 60;
const MAX_COLOR_LENGTH = 30;
const MAX_NOTES_LENGTH = 1000;
//: Matches the API's own bound (1900 to the current year + 1).
const MIN_YEAR = 1900;
const MAX_YEAR = new Date().getFullYear() + 1;

export interface VehicleFormInitialValues {
  vehicleType: VehicleType;
  make: string;
  model: string;
  year: string;
  color: string;
  plate: string;
  notes: string;
}

export interface VehicleFormValues {
  vehicleType: VehicleType;
  make: string;
  model: string;
  year: number | null;
  color: string;
  plate: string;
  notes: string;
}

export interface VehicleFormProps {
  mode: "create" | "edit";
  initialValues?: Partial<VehicleFormInitialValues>;
  onSubmit: (values: VehicleFormValues) => void;
  pending: boolean;
  errorMessage?: string;
  submitLabel: string;
  submitPendingLabel: string;
  /** Disables submission with an explanation: creating/editing vehicles needs a connection in this MVP. */
  offline?: boolean;
}

/**
 * Presentational, shared by the create and edit vehicle screens. Owns
 * every field's local state; `onSubmit` only ever receives already
 * trimmed, already parsed values (create sends them all; edit diffs
 * against the current vehicle and PATCHes only what changed). The plate
 * is normalized server-side (`normalize_plate`), so this form sends it
 * through untouched beyond trimming.
 */
export function VehicleForm({
  mode,
  initialValues,
  onSubmit,
  pending,
  errorMessage,
  submitLabel,
  submitPendingLabel,
  offline = false,
}: VehicleFormProps) {
  const [vehicleType, setVehicleType] = useState<VehicleType>(initialValues?.vehicleType ?? "car");
  const [make, setMake] = useState(initialValues?.make ?? "");
  const [model, setModel] = useState(initialValues?.model ?? "");
  const [year, setYear] = useState(initialValues?.year ?? "");
  const [color, setColor] = useState(initialValues?.color ?? "");
  const [plate, setPlate] = useState(initialValues?.plate ?? "");
  const [notes, setNotes] = useState(initialValues?.notes ?? "");
  const [makeTouched, setMakeTouched] = useState(false);
  const [yearTouched, setYearTouched] = useState(false);

  const trimmedMake = make.trim();
  const makeMissing = trimmedMake.length === 0;
  const makeTooLong = trimmedMake.length > MAX_MAKE_LENGTH;
  const makeInvalid = makeMissing || makeTooLong;

  const trimmedYear = year.trim();
  const parsedYear = trimmedYear === "" ? null : Number(trimmedYear);
  const yearInvalid =
    trimmedYear !== "" &&
    (parsedYear === null ||
      !Number.isInteger(parsedYear) ||
      parsedYear < MIN_YEAR ||
      parsedYear > MAX_YEAR);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMakeTouched(true);
    setYearTouched(true);
    if (makeInvalid || yearInvalid) {
      return;
    }
    if (offline) {
      return;
    }
    onSubmit({
      vehicleType,
      make: trimmedMake,
      model: model.trim(),
      year: parsedYear,
      color: color.trim(),
      plate: plate.trim(),
      notes: notes.trim(),
    });
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      {errorMessage ? <Alert variant="error">{errorMessage}</Alert> : null}
      {offline ? (
        <Alert variant="info">
          {mode === "create"
            ? customersCopy.vehicles.offline.createDisabled
            : customersCopy.vehicles.offline.editDisabled}
        </Alert>
      ) : null}
      <div className="flex flex-col gap-1.5">
        <label htmlFor="vehicle_type" className="text-base font-medium text-brand-foreground">
          {customersCopy.vehicles.form.typeLabel}
        </label>
        <select
          id="vehicle_type"
          value={vehicleType}
          onChange={(event) => setVehicleType(event.target.value as VehicleType)}
          className="min-h-12 rounded-xl border border-brand-border px-4 text-base text-brand-foreground outline-none focus:ring-2 focus:ring-brand-accent"
        >
          <option value="car">{customersCopy.vehicles.typeLabels.car}</option>
          <option value="motorcycle">{customersCopy.vehicles.typeLabels.motorcycle}</option>
          <option value="other">{customersCopy.vehicles.typeLabels.other}</option>
        </select>
      </div>
      <TextField
        label={customersCopy.vehicles.form.makeLabel}
        name="make"
        value={make}
        onChange={(event) => setMake(event.target.value)}
        onBlur={() => setMakeTouched(true)}
        error={
          makeTouched && makeMissing
            ? customersCopy.vehicles.form.makeRequired
            : makeTouched && makeTooLong
              ? customersCopy.vehicles.form.makeTooLong
              : undefined
        }
        maxLength={MAX_MAKE_LENGTH + 1}
        required
      />
      <TextField
        label={customersCopy.vehicles.form.modelLabel}
        name="model"
        value={model}
        onChange={(event) => setModel(event.target.value)}
        maxLength={MAX_MODEL_LENGTH + 1}
      />
      <TextField
        label={customersCopy.vehicles.form.yearLabel}
        name="year"
        type="text"
        inputMode="numeric"
        value={year}
        onChange={(event) => setYear(event.target.value)}
        onBlur={() => setYearTouched(true)}
        error={yearTouched && yearInvalid ? customersCopy.vehicles.form.yearInvalid : undefined}
        helperText={customersCopy.vehicles.form.yearHelper}
      />
      <TextField
        label={customersCopy.vehicles.form.colorLabel}
        name="color"
        value={color}
        onChange={(event) => setColor(event.target.value)}
        maxLength={MAX_COLOR_LENGTH + 1}
      />
      <TextField
        label={customersCopy.vehicles.form.plateLabel}
        name="plate"
        value={plate}
        onChange={(event) => setPlate(event.target.value)}
        helperText={customersCopy.vehicles.form.plateHelper}
      />
      <TextArea
        label={customersCopy.vehicles.form.notesLabel}
        name="notes"
        value={notes}
        onChange={(event) => setNotes(event.target.value)}
        maxLength={MAX_NOTES_LENGTH + 1}
      />
      <Button type="submit" loading={pending} disabled={offline || pending}>
        {pending ? submitPendingLabel : submitLabel}
      </Button>
    </form>
  );
}
