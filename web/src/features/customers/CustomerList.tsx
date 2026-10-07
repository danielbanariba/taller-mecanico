import { customersCopy } from "./copy";
import type { CustomerOut } from "./api";

export interface CustomerListProps {
  customers: CustomerOut[];
  isFiltered: boolean;
  onOpen: (customer: CustomerOut) => void;
}

/** Presentational: the customers list, with empty and filtered-empty states. */
export function CustomerList({ customers, isFiltered, onOpen }: CustomerListProps) {
  if (customers.length === 0) {
    return (
      <div className="flex flex-col items-center gap-1 rounded-2xl border border-dashed border-brand-border px-4 py-10 text-center">
        <p className="text-lg font-semibold text-brand-foreground">
          {isFiltered ? customersCopy.list.emptyFilteredTitle : customersCopy.list.emptyTitle}
        </p>
        <p className="text-base text-brand-muted-foreground">
          {isFiltered ? customersCopy.list.emptyFilteredBody : customersCopy.list.emptyBody}
        </p>
      </div>
    );
  }

  return (
    <ul className="flex flex-col gap-2">
      {customers.map((customer) => (
        <li key={customer.id}>
          <button
            type="button"
            onClick={() => onOpen(customer)}
            className="flex w-full flex-col items-start gap-0.5 rounded-2xl border border-brand-border bg-brand-card px-4 py-3 text-left"
          >
            <span className="text-lg font-semibold text-brand-foreground">{customer.full_name}</span>
            {customer.phone ? (
              <span className="text-sm text-brand-muted-foreground">
                {customer.phone}
                {customer.phone_is_mobile === true
                  ? ` · ${customersCopy.list.mobileBadge}`
                  : customer.phone_is_mobile === false
                    ? ` · ${customersCopy.list.landlineBadge}`
                    : ""}
              </span>
            ) : null}
          </button>
        </li>
      ))}
    </ul>
  );
}
