import { useState, type FormEvent } from "react";

import { Alert } from "../../shared/ui/Alert";
import { Button } from "../../shared/ui/Button";
import { TextField } from "../../shared/ui/TextField";
import { authCopy } from "./copy";
import type { LoginPayload } from "./api";

export interface LoginFormProps {
  onSubmit: (payload: LoginPayload) => void;
  pending: boolean;
  errorMessage?: string;
}

/** Presentational: owns only the two input values, nothing else. */
export function LoginForm({ onSubmit, pending, errorMessage }: LoginFormProps) {
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
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
