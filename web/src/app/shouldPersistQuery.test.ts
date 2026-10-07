import { describe, expect, it } from "vitest";
import { dehydrate, QueryClient } from "@tanstack/react-query";

import { shouldPersistQuery } from "./shouldPersistQuery";

describe("shouldPersistQuery", () => {
  it("drops a query marked meta: { persist: false } from the persisted snapshot, keeping every other query with data", async () => {
    // Defect this catches: the daily cash summary's stale totals
    // surviving into the persisted IndexedDB cache and rendering as
    // current on reload, which AD-17 forbids -- the summary must always
    // be a live read.
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    await queryClient.prefetchQuery({ queryKey: ["items"], queryFn: () => Promise.resolve({ ok: true }) });
    await queryClient.prefetchQuery({
      queryKey: ["cashSummary", "2026-10-07"],
      queryFn: () => Promise.resolve({ total_cents: 100 }),
      meta: { persist: false },
    });

    const dehydrated = dehydrate(queryClient, { shouldDehydrateQuery: shouldPersistQuery });

    expect(dehydrated.queries.map((entry) => entry.queryKey)).toEqual([["items"]]);
  });

  it("still keeps a query that holds data from a failed background refetch", () => {
    // Defect this catches: adding the new `meta.persist` check accidentally
    // narrowing the pre-existing "keep data from a failed refetch" rule
    // the offline cache depends on (see `AppProviders`'s own comment).
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    queryClient.setQueryData(["items"], { ok: true });

    const dehydrated = dehydrate(queryClient, { shouldDehydrateQuery: shouldPersistQuery });

    expect(dehydrated.queries.map((entry) => entry.queryKey)).toEqual([["items"]]);
  });
});
