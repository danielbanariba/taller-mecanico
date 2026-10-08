import { useState, type FormEvent } from "react";

import { Alert } from "../../../shared/ui/Alert";
import { Button } from "../../../shared/ui/Button";
import { TextField } from "../../../shared/ui/TextField";
import { invoicingCopy } from "../copy";

export interface FiscalProfileFormValues {
  rtn: string;
  legalName: string;
  tradeName: string;
  address: string;
  phone: string;
  email: string;
  establishmentCode: string;
  emissionPointCode: string;
}

export interface FiscalProfileFormProps {
  initialValues?: Partial<FiscalProfileFormValues>;
  onSubmit: (values: FiscalProfileFormValues) => void;
  pending: boolean;
  errorMessage?: string;
  /** Disables submission with an explanation: saving the fiscal profile needs a connection (`fiscal-profile` spec). */
  offline?: boolean;
}

/**
 * Presentational: every Art. 10-11 issuer field (AD-3), all of them
 * mandatory -- `PUT /invoicing/profile` requires all eight, so a stored
 * profile is always complete. Client-side validation only checks that
 * every field was filled in; format validation (RTN digit count, email
 * shape, 3-digit codes) is the server's, surfaced through `errorMessage`.
 */
export function FiscalProfileForm({
  initialValues,
  onSubmit,
  pending,
  errorMessage,
  offline = false,
}: FiscalProfileFormProps) {
  const [rtn, setRtn] = useState(initialValues?.rtn ?? "");
  const [legalName, setLegalName] = useState(initialValues?.legalName ?? "");
  const [tradeName, setTradeName] = useState(initialValues?.tradeName ?? "");
  const [address, setAddress] = useState(initialValues?.address ?? "");
  const [phone, setPhone] = useState(initialValues?.phone ?? "");
  const [email, setEmail] = useState(initialValues?.email ?? "");
  const [establishmentCode, setEstablishmentCode] = useState(initialValues?.establishmentCode ?? "");
  const [emissionPointCode, setEmissionPointCode] = useState(initialValues?.emissionPointCode ?? "");
  const [touched, setTouched] = useState(false);

  const trimmed = {
    rtn: rtn.trim(),
    legalName: legalName.trim(),
    tradeName: tradeName.trim(),
    address: address.trim(),
    phone: phone.trim(),
    email: email.trim(),
    establishmentCode: establishmentCode.trim(),
    emissionPointCode: emissionPointCode.trim(),
  };
  const hasEmptyField = Object.values(trimmed).some((value) => value.length === 0);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setTouched(true);
    if (hasEmptyField || offline) {
      return;
    }
    onSubmit(trimmed);
  }

  const copy = invoicingCopy.settings.profileForm;

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      {errorMessage ? <Alert variant="error">{errorMessage}</Alert> : null}
      {offline ? <Alert variant="info">{invoicingCopy.offline.profileWriteDisabled}</Alert> : null}
      <TextField
        label={copy.legalNameLabel}
        name="legal_name"
        value={legalName}
        onChange={(event) => setLegalName(event.target.value)}
        error={touched && trimmed.legalName.length === 0 ? copy.legalNameRequired : undefined}
        required
      />
      <TextField
        label={copy.tradeNameLabel}
        name="trade_name"
        value={tradeName}
        onChange={(event) => setTradeName(event.target.value)}
        error={touched && trimmed.tradeName.length === 0 ? copy.tradeNameRequired : undefined}
        required
      />
      <TextField
        label={copy.rtnLabel}
        name="rtn"
        value={rtn}
        onChange={(event) => setRtn(event.target.value)}
        error={touched && trimmed.rtn.length === 0 ? copy.rtnRequired : undefined}
        helperText={copy.rtnHelper}
        required
      />
      <TextField
        label={copy.addressLabel}
        name="address"
        value={address}
        onChange={(event) => setAddress(event.target.value)}
        error={touched && trimmed.address.length === 0 ? copy.addressRequired : undefined}
        required
      />
      <TextField
        label={copy.phoneLabel}
        name="phone"
        type="tel"
        value={phone}
        onChange={(event) => setPhone(event.target.value)}
        error={touched && trimmed.phone.length === 0 ? copy.phoneRequired : undefined}
        required
      />
      <TextField
        label={copy.emailLabel}
        name="email"
        type="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        error={touched && trimmed.email.length === 0 ? copy.emailRequired : undefined}
        required
      />
      <TextField
        label={copy.establishmentCodeLabel}
        name="establishment_code"
        value={establishmentCode}
        onChange={(event) => setEstablishmentCode(event.target.value)}
        error={touched && trimmed.establishmentCode.length === 0 ? copy.establishmentCodeRequired : undefined}
        helperText={copy.establishmentCodeHelper}
        required
      />
      <TextField
        label={copy.emissionPointCodeLabel}
        name="emission_point_code"
        value={emissionPointCode}
        onChange={(event) => setEmissionPointCode(event.target.value)}
        error={touched && trimmed.emissionPointCode.length === 0 ? copy.emissionPointCodeRequired : undefined}
        helperText={copy.emissionPointCodeHelper}
        required
      />
      <Button type="submit" loading={pending} disabled={offline || pending}>
        {pending ? copy.submitPending : copy.submit}
      </Button>
    </form>
  );
}
