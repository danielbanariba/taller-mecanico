import { invoicingCopy } from "../copy";

/**
 * In-app SAR registration notice (`fiscal-profile` spec, "The Settings
 * Screen Shows The In-App SAR Registration Notice"): registering the
 * system with SAR and the Declaración Jurada (Art. 47, 53), confirming
 * the module with the workshop's own contador, and certified thermal
 * paper if printing on 58 mm (Art. 38). Shown unconditionally -- whether
 * or not a profile exists yet -- never only after it is complete.
 */
export function SarNotice() {
  return (
    <div className="flex flex-col gap-2 rounded-xl border border-brand-border p-4">
      <p className="text-sm text-brand-foreground">{invoicingCopy.settings.sarNotice.registration}</p>
      <p className="text-sm text-brand-foreground">{invoicingCopy.settings.sarNotice.accountant}</p>
      <p className="text-sm text-brand-foreground">{invoicingCopy.settings.sarNotice.thermalPaper}</p>
    </div>
  );
}
