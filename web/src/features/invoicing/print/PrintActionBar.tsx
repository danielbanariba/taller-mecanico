import { Button } from "../../../shared/ui/Button";
import { invoicingCopy } from "../copy";

export interface PrintActionBarProps {
  onlyOriginal: boolean;
  onToggleOnlyOriginal: (value: boolean) => void;
}

/**
 * `print:hidden` action bar shared by both invoice print layouts: the
 * print trigger and the "Solo original" toggle that drops the issuer's
 * copy for a reprint (AD-16's "Original and copy").
 */
export function PrintActionBar({ onlyOriginal, onToggleOnlyOriginal }: PrintActionBarProps) {
  return (
    <div className="flex flex-col gap-3 print:hidden sm:flex-row sm:items-center sm:justify-between">
      <Button variant="secondary" onClick={() => window.print()}>
        {invoicingCopy.print.printAction}
      </Button>
      <label className="flex items-center gap-2 text-base text-brand-foreground">
        <input
          type="checkbox"
          checked={onlyOriginal}
          onChange={(event) => onToggleOnlyOriginal(event.target.checked)}
        />
        {invoicingCopy.print.onlyOriginalToggle}
      </label>
    </div>
  );
}
