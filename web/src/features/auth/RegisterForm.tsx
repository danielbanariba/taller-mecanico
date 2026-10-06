import { useState, type FormEvent } from "react";

import { Alert } from "../../shared/ui/Alert";
import { Button } from "../../shared/ui/Button";
import { TextField } from "../../shared/ui/TextField";
import { authCopy } from "./copy";
import type { RegisterPayload } from "./api";

export interface RegisterFormProps {
  onSubmit: (payload: RegisterPayload) => void;
  pending: boolean;
  errorMessage?: string;
}

const MIN_PASSWORD_LENGTH = 8;
const MAX_PASSWORD_LENGTH = 128;

/**
 * Presentational, except for the client-side rules worth enforcing before
 * spending a round trip: password length, both bounds. `maxLength` on the
 * input stops typing past the limit, but a pasted or programmatically set
 * value can still exceed it, so the length check here is the one that
 * actually blocks submission. Everything else (phone format, duplicate
 * phone) is the API's call.
 */
export function RegisterForm({ onSubmit, pending, errorMessage }: RegisterFormProps) {
  const [workshopName, setWorkshopName] = useState("");
  const [ownerName, setOwnerName] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [passwordTouched, setPasswordTouched] = useState(false);

  const passwordTooShort = password.length > 0 && password.length < MIN_PASSWORD_LENGTH;
  const passwordTooLong = password.length > MAX_PASSWORD_LENGTH;
  const passwordError = passwordTooShort
    ? authCopy.register.passwordTooShort
    : passwordTooLong
      ? authCopy.register.passwordTooLong
      : undefined;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPasswordTouched(true);
    if (password.length < MIN_PASSWORD_LENGTH || password.length > MAX_PASSWORD_LENGTH) {
      return;
    }
    onSubmit({ workshop_name: workshopName, owner_name: ownerName, phone, password });
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      {errorMessage ? <Alert variant="error">{errorMessage}</Alert> : null}
      <TextField
        label={authCopy.register.workshopNameLabel}
        name="workshop_name"
        autoComplete="organization"
        value={workshopName}
        onChange={(event) => setWorkshopName(event.target.value)}
        required
      />
      <TextField
        label={authCopy.register.ownerNameLabel}
        name="owner_name"
        autoComplete="name"
        value={ownerName}
        onChange={(event) => setOwnerName(event.target.value)}
        required
      />
      <TextField
        label={authCopy.register.phoneLabel}
        name="phone"
        type="tel"
        inputMode="numeric"
        autoComplete="tel"
        placeholder={authCopy.register.phonePlaceholder}
        value={phone}
        onChange={(event) => setPhone(event.target.value)}
        required
      />
      <TextField
        label={authCopy.register.passwordLabel}
        name="password"
        type="password"
        autoComplete="new-password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        onBlur={() => setPasswordTouched(true)}
        maxLength={MAX_PASSWORD_LENGTH}
        error={passwordTouched ? passwordError : undefined}
        helperText={authCopy.register.passwordHelper}
        required
      />
      <Button type="submit" loading={pending} disabled={pending}>
        {pending ? authCopy.register.submitPending : authCopy.register.submit}
      </Button>
    </form>
  );
}
