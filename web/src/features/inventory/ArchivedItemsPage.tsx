import { useMemo } from "react";
import { Link } from "react-router";

import { LinkButton } from "../../shared/ui/LinkButton";
import { Spinner } from "../../shared/ui/Spinner";
import { inventoryCopy } from "./copy";
import { useItems } from "./hooks";

/**
 * Container: the read-only list of archived items. Each row links to the
 * normal detail screen, where "Restaurar" lives (`ItemDetailPage.tsx`) --
 * this page itself never mutates anything.
 *
 * `useItems({ includeArchived: true })` returns both active and archived
 * items (the same param the default inventory list already supports), so
 * this filters down to archived ones client-side rather than adding a
 * second list endpoint shape.
 */
export function ArchivedItemsPage() {
  const items = useItems({ includeArchived: true });
  const archivedItems = useMemo(
    () => (items.data ?? []).filter((item) => item.archived_at !== null),
    [items.data],
  );

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold text-brand-primary">{inventoryCopy.archived.title}</h1>

      <LinkButton to="/inventario" variant="secondary">
        {inventoryCopy.detail.backToList}
      </LinkButton>

      {items.isPending ? (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      ) : archivedItems.length === 0 ? (
        <p className="text-base text-brand-muted-foreground">{inventoryCopy.archived.empty}</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {archivedItems.map((item) => (
            <li key={item.id}>
              <Link
                to={`/inventario/${item.id}`}
                className="block rounded-2xl border border-brand-border bg-brand-card p-3"
              >
                <p className="text-lg font-semibold text-brand-foreground">{item.name}</p>
                {[item.category, item.unit].filter(Boolean).join(" · ") ? (
                  <p className="text-sm text-brand-muted-foreground">
                    {[item.category, item.unit].filter(Boolean).join(" · ")}
                  </p>
                ) : null}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
