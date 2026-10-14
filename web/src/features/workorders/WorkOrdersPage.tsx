import { useRef, useState, type KeyboardEvent } from "react";
import { useNavigate } from "react-router";

import { ApiError } from "../../shared/api/http";
import { useOnlineStatus } from "../../shared/offline/useOnlineStatus";
import { Alert } from "../../shared/ui/Alert";
import { Button } from "../../shared/ui/Button";
import { Spinner } from "../../shared/ui/Spinner";
import { workOrdersCopy } from "./copy";
import { useWorkOrders } from "./hooks";
import { WorkOrderList } from "./WorkOrderList";
import type { StatusGroup } from "./api";

const TABS: { group: StatusGroup; label: string }[] = [
  { group: "open", label: workOrdersCopy.list.tabOpen },
  { group: "closed", label: workOrdersCopy.list.tabHistory },
];

function tabClassName(isActive: boolean): string {
  return `flex-1 rounded-xl px-4 py-2 text-base font-medium ${
    isActive ? "bg-brand-accent text-brand-on-accent" : "bg-brand-muted text-brand-muted-foreground"
  }`;
}

/** Container: the work orders list, split into the Abiertas and Historial tabs. Status actions and search arrive in later slices. */
export function WorkOrdersPage() {
  const navigate = useNavigate();
  const isOffline = useOnlineStatus();
  const [statusGroup, setStatusGroup] = useState<StatusGroup>("open");
  const orders = useWorkOrders(statusGroup);
  const flatOrders = orders.data?.pages.flat() ?? [];
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);

  // No cached page AND the reason is connectivity: either already offline,
  // or the first fetch already settled into `network_error`. Without this,
  // a cold load that starts offline falls through to `WorkOrderList`'s own
  // empty state ("Todavía no hay órdenes") -- indistinguishable from a
  // workshop that genuinely has none (a QA sweep finding, the same bug
  // `NewWorkOrderPage`'s customer/vehicle steps had).
  const ordersUnavailable =
    orders.data === undefined &&
    (isOffline || (orders.error instanceof ApiError && orders.error.code === "network_error"));

  // ARIA tabs roving-tabindex pattern: only the selected tab is in the tab
  // order (`tabIndex 0`); the arrows move focus AND selection together,
  // wrapping past either end, so a screen-reader/keyboard user never has
  // to Tab through every tab one at a time.
  function handleTabKeyDown(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") {
      return;
    }
    event.preventDefault();
    const direction = event.key === "ArrowRight" ? 1 : -1;
    const nextIndex = (index + direction + TABS.length) % TABS.length;
    setStatusGroup(TABS[nextIndex].group);
    tabRefs.current[nextIndex]?.focus();
  }

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold text-brand-primary">{workOrdersCopy.list.title}</h1>

      <Button onClick={() => navigate("/ordenes/nueva")}>{workOrdersCopy.list.newOrder}</Button>

      <div role="tablist" className="flex gap-2">
        {TABS.map(({ group, label }, index) => (
          <button
            key={group}
            ref={(node) => {
              tabRefs.current[index] = node;
            }}
            type="button"
            role="tab"
            aria-selected={statusGroup === group}
            tabIndex={statusGroup === group ? 0 : -1}
            onClick={() => setStatusGroup(group)}
            onKeyDown={(event) => handleTabKeyDown(event, index)}
            className={tabClassName(statusGroup === group)}
          >
            {label}
          </button>
        ))}
      </div>

      {ordersUnavailable ? (
        <Alert variant="info">{workOrdersCopy.offline.listDisabled}</Alert>
      ) : orders.isPending ? (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      ) : (
        <WorkOrderList orders={flatOrders} onOpen={(order) => navigate(`/ordenes/${order.id}`)} />
      )}

      {orders.hasNextPage ? (
        <Button variant="secondary" onClick={() => orders.fetchNextPage()} loading={orders.isFetchingNextPage}>
          {workOrdersCopy.list.loadMore}
        </Button>
      ) : null}
    </div>
  );
}
