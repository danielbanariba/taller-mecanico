import { useState } from "react";
import { useNavigate } from "react-router";

import { ApiError } from "../../shared/api/http";
import { useOnlineStatus } from "../../shared/offline/useOnlineStatus";
import { Alert } from "../../shared/ui/Alert";
import { Button } from "../../shared/ui/Button";
import { Spinner } from "../../shared/ui/Spinner";
import { TextField } from "../../shared/ui/TextField";
import { CustomerList } from "./CustomerList";
import { customersCopy } from "./copy";
import { useCustomers, useDebouncedValue } from "./hooks";

const SEARCH_DEBOUNCE_MS = 300;

/** Container: the customers list and search. */
export function CustomersPage() {
  const navigate = useNavigate();
  const isOffline = useOnlineStatus();
  const [searchInput, setSearchInput] = useState("");
  const debouncedQuery = useDebouncedValue(searchInput, SEARCH_DEBOUNCE_MS);

  const customers = useCustomers({ q: debouncedQuery.trim() || undefined });
  const isFiltered = debouncedQuery.trim().length > 0;

  // No cached data AND the reason is connectivity: either already offline,
  // or the first fetch already settled into `network_error`. Without this,
  // a cold load that starts offline falls through to `CustomerList`'s own
  // empty state ("Todavía no hay clientes") -- indistinguishable from a
  // workshop that genuinely has none (a QA sweep finding, the same bug
  // `NewWorkOrderPage`'s customer/vehicle steps had).
  const customersUnavailable =
    customers.data === undefined &&
    (isOffline || (customers.error instanceof ApiError && customers.error.code === "network_error"));

  return (
    <>
      <TextField
        label={customersCopy.list.searchLabel}
        placeholder={customersCopy.list.searchPlaceholder}
        value={searchInput}
        onChange={(event) => setSearchInput(event.target.value)}
      />

      <Button onClick={() => navigate("/clientes/nuevo")}>{customersCopy.list.addCustomer}</Button>

      {customersUnavailable ? (
        <Alert variant="info">{customersCopy.offline.listDisabled}</Alert>
      ) : customers.isPending ? (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      ) : (
        <CustomerList
          customers={customers.data ?? []}
          isFiltered={isFiltered}
          onOpen={(customer) => navigate(`/clientes/${customer.id}`)}
        />
      )}
    </>
  );
}
