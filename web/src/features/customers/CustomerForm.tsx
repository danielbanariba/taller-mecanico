import { useState, type FormEvent } from "react";

import { Alert } from "../../shared/ui/Alert";
import { Button } from "../../shared/ui/Button";
import { TextArea } from "../../shared/ui/TextArea";
import { TextField } from "../../shared/ui/TextField";
import { customersCopy } from "./copy";

const MAX_NAME_LENGTH = 120;
const MAX_NOTES_LENGTH = 1000;

export interface CustomerFormInitialValues {
  fullName: string;
  phone: string;
  notes: string;
}

export interface CustomerFormValues {
  fullName: string;
  phone: string;
  notes: string;
}

export interface CustomerFormProps {
  mode: "create" | "edit";
  initialValues?: Partial<CustomerFormInitialValues>;
  onSubmit: (values: CustomerFormValues) => void;
  pending: boolean;
  errorMessage?: string;
  submitLabel: string;
  submitPendingLabel: string;
  /** Disables submission with an explanation: creating/editing customers needs a connection in this MVP. */
  offline?: boolean;
}

/**
 * Presentational, shared by the create and edit screens. Owns every
 * field's local state; `onSubmit` only ever receives already-trimmed
 * values (create sends them all; edit diffs against the current customer
 * and PATCHes only what changed).
 */
export function CustomerForm({
  mode,
  initialValues,
  onSubmit,
  pending,
  errorMessage,
  submitLabel,
  submitPendingLabel,
  offline = false,
}: CustomerFormProps) {
  const [fullName, setFullName] = useState(initialValues?.fullName ?? "");
  const [phone, setPhone] = useState(initialValues?.phone ?? "");
  const [notes, setNotes] = useState(initialValues?.notes ?? "");
  const [nameTouched, setNameTouched] = useState(false);

  const trimmedName = fullName.trim();
  const nameMissing = trimmedName.length === 0;
  const nameTooLong = trimmedName.length > MAX_NAME_LENGTH;
  const nameInvalid = nameMissing || nameTooLong;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setNameTouched(true);
    if (nameInvalid) {
      return;
    }
    if (offline) {
      return;
    }
    onSubmit({ fullName: trimmedName, phone: phone.trim(), notes: notes.trim() });
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      {errorMessage ? <Alert variant="error">{errorMessage}</Alert> : null}
      {offline ? (
        <Alert variant="info">
          {mode === "create" ? customersCopy.offline.createDisabled : customersCopy.offline.editDisabled}
        </Alert>
      ) : null}
      <TextField
        label={customersCopy.form.nameLabel}
        name="full_name"
        value={fullName}
        onChange={(event) => setFullName(event.target.value)}
        onBlur={() => setNameTouched(true)}
        error={
          nameTouched && nameMissing
            ? customersCopy.form.nameRequired
            : nameTouched && nameTooLong
              ? customersCopy.form.nameTooLong
              : undefined
        }
        maxLength={MAX_NAME_LENGTH + 1}
        required
      />
      <TextField
        label={customersCopy.form.phoneLabel}
        name="phone"
        type="tel"
        value={phone}
        onChange={(event) => setPhone(event.target.value)}
        helperText={customersCopy.form.phoneHelper}
      />
      <TextArea
        label={customersCopy.form.notesLabel}
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
