import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { ItemList } from "./ItemList";
import type { ItemOut } from "./api";

function buildItem(index: number): ItemOut {
  return {
    id: `item-${index}`,
    name: `Repuesto ${index}`,
    category: "Filtros",
    unit: "unidad",
    min_stock: 0,
    sale_price_cents: null,
    notes: null,
    stock: 10,
    needs_review: false,
    is_low: false,
    archived_at: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  };
}

const noop = () => {};

describe("ItemList", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  /**
   * jsdom has no layout engine: every element's `offsetHeight` is always
   * 0 (the same long-standing jsdom limitation `Receipt58Page.test.tsx`
   * and `ThermalPageStyle.test.tsx` already work around for
   * `getBoundingClientRect`, a sibling measurement). `@tanstack/react-virtual`'s
   * default row measurement (`measureElement` in `virtual-core`) falls
   * back to `element.offsetHeight` once a row's ref attaches, so every
   * rendered row measures 0px here. With every mounted row reporting 0,
   * the virtualizer keeps growing the rendered range trying to fill a
   * viewport that mounting more 0px rows can never fill -- observed
   * directly while building this test: it rendered roughly half of a
   * 300-item list, and threw React's "Maximum update depth exceeded" for
   * a 3000-item one. Neither happens in a real browser, where a row's
   * real height is never 0. Stubbing a plausible, fixed row height here
   * restores the real behavior this test needs to observe: a small,
   * stable set of rows near the viewport, not the whole list.
   */
  function stubRowHeight(px: number) {
    vi.spyOn(HTMLElement.prototype, "offsetHeight", "get").mockReturnValue(px);
  }

  it("mounts far fewer rows than the full list for a few hundred items", () => {
    // Defect this catches: the inventory list rendering every item
    // unconditionally instead of only the rows near the viewport -- the
    // regression the QA sweep found at 3000 items (27.6k DOM nodes, the
    // main thread blocked 46-99% of the time while scrolling under CPU
    // throttling). This fails the moment `ItemList` goes back to mapping
    // every item into the DOM, because `rows.length` would then equal
    // `items.length` instead of staying a small, bounded window.
    stubRowHeight(96);
    const items = Array.from({ length: 300 }, (_, index) => buildItem(index));

    render(<ItemList items={items} onOpen={noop} onIncrement={noop} onDecrement={noop} />);

    const rows = screen.getAllByRole("listitem");
    expect(rows.length).toBeGreaterThan(0);
    expect(rows.length).toBeLessThan(items.length / 4);
  });

  it("renders the tapped item's content inside a visible row", () => {
    // Defect this catches: wiring the virtualizer's windowing so that the
    // rows it does mount no longer correspond to the right items (e.g. an
    // off-by-one in `virtualRow.index`, or passing the wrong item into
    // `ItemRow`).
    stubRowHeight(96);
    const items = Array.from({ length: 50 }, (_, index) => buildItem(index));

    render(<ItemList items={items} onOpen={noop} onIncrement={noop} onDecrement={noop} />);

    expect(screen.getByText("Repuesto 0")).toBeInTheDocument();
  });
});
