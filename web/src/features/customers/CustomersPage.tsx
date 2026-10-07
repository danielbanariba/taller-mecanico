import { useState } from "react";
import { useNavigate } from "react-router";

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
  const [searchInput, setSearchInput] = useState("");
  const debouncedQuery = useDebouncedValue(searchInput, SEARCH_DEBOUNCE_MS);

  const customers = useCustomers({ q: debouncedQuery.trim() || undefined });
  const isFiltered = debouncedQuery.trim().length > 0;

  return (
    <>
      <TextField
        label={customersCopy.list.searchLabel}
        placeholder={customersCopy.list.searchPlaceholder}
        value={searchInput}
        onChange={(event) => setSearchInput(event.target.value)}
      />

      <Button onClick={() => navigate("/clientes/nuevo")}>{customersCopy.list.addCustomer}</Button>

      {customers.isPending ? (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      ) : (
        <CustomerList
          customers={customers.data ?? []}
          isFiltered={isFiltered}
          onOpen={(customer) => navigate(`/clientes/${customer.id}/editar`)}
        />
      )}
    </>
  );
}
