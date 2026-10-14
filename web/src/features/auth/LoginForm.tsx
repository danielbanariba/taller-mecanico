import { useState, type FormEvent } from "react";

import { isValidPhone } from "../../shared/format/phone";
import { Alert } from "../../shared/ui/Alert";
import { Button } from "../../shared/ui/Button";
import { TextField } from "../../shared/ui/TextField";
import { authCopy } from "./copy";
import type { LoginPayload } from "./api";

export interface LoginFormProps {
  onSubmit: (payload: LoginPayload) => void;
  pending: boolean;
  errorMessage?: string;
  /** Seeds the fields once on mount; the user can still edit them. */
  initialValues?: Partial<LoginPayload>;
}

/**
 * Presentational, except for the one client-side rule worth enforcing
 * before spending a round trip: the phone shape, mirroring the API's own
 * `PhoneNumber` rule exactly (`isValidPhone`). Everything else (whether
 * that phone/password combination is correct) is the API's call.
 */
export function LoginForm({ onSubmit, pending, errorMessage, initialValues }: LoginFormProps) {
  const [phone, setPhone] = useState(initialValues?.phone ?? "");
  const [password, setPassword] = useState(initialValues?.password ?? "");
  const [phoneTouched, setPhoneTouched] = useState(false);

  const phoneError = phoneTouched && !isValidPhone(phone) ? authCopy.login.phoneInvalid : undefined;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPhoneTouched(true);
    if (!isValidPhone(phone)) {
      return;
    }
    onSubmit({ phone, password });
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      {errorMessage ? <Alert variant="error">{errorMessage}</Alert> : null}
      <TextField
        label={authCopy.login.phoneLabel}
        name="phone"
        type="tel"
        inputMode="numeric"
        autoComplete="tel"
        placeholder={authCopy.login.phonePlaceholder}
        value={phone}
        onChange={(event) => setPhone(event.target.value)}
        onBlur={() => setPhoneTouched(true)}
        error={phoneError}
        required
      />
      <TextField
        label={authCopy.login.passwordLabel}
        name="password"
        type="password"
        autoComplete="current-password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        required
      />
      <Button type="submit" loading={pending} disabled={pending}>
        {pending ? authCopy.login.submitPending : authCopy.login.submit}
      </Button>
    </form>
  );
}
