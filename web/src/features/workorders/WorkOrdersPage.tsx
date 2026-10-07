import { useState } from "react";
import { useNavigate } from "react-router";

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
  const [statusGroup, setStatusGroup] = useState<StatusGroup>("open");
  const orders = useWorkOrders(statusGroup);
  const flatOrders = orders.data?.pages.flat() ?? [];

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold text-brand-primary">{workOrdersCopy.list.title}</h1>

      <div role="tablist" className="flex gap-2">
        {TABS.map(({ group, label }) => (
          <button
            key={group}
            type="button"
            role="tab"
            aria-selected={statusGroup === group}
            onClick={() => setStatusGroup(group)}
            className={tabClassName(statusGroup === group)}
          >
            {label}
          </button>
        ))}
      </div>

      {orders.isPending ? (
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
