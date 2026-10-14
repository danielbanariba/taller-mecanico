import { useLayoutEffect, useRef, useState } from "react";
import { useWindowVirtualizer } from "@tanstack/react-virtual";

import type { ItemOut } from "./api";
import { ItemRow } from "./ItemRow";

export interface ItemListProps {
  items: ItemOut[];
  onOpen: (item: ItemOut) => void;
  onIncrement: (item: ItemOut) => void;
  onDecrement: (item: ItemOut) => void;
}

/**
 * A plausible row height used only until `measureElement` reports the real
 * one. Measured at 375px wide (a QA sweep recheck of the local production
 * build): `ItemRow` renders at ~132px there, not the 96px this previously
 * assumed, so the virtualizer's total scroll height grew ~6.6% while
 * scrolling and the scrollbar thumb visibly jumped as real rows replaced
 * the too-short estimate.
 */
const ESTIMATED_ROW_HEIGHT_PX = 132;
const OVERSCAN_ROWS = 8;

/**
 * Presentational: window-virtualized rendering of the inventory list.
 *
 * At 3000 items the plain `<ul>` this replaced put 27.6k DOM nodes on the
 * page; scrolling it under 4x CPU throttling blocked the main thread
 * 46-99% of the time, with a ~954ms longest task (QA sweep T3).
 * `useWindowVirtualizer` keeps only the rows near the viewport mounted,
 * so the DOM node count no longer grows with the inventory size.
 *
 * The page itself scrolls the window -- `AppShell`'s `<main>` has no
 * `overflow` of its own, so the browser's own scrollbar moves the whole
 * document -- not an inner scroll container, so this uses
 * `useWindowVirtualizer` (not `useVirtualizer`). `scrollMargin` corrects
 * the virtualizer's offset math for how far this `<ul>` sits from the
 * top of the document (the search field, filter chips and "Agregar
 * repuesto" button above it in `InventoryPage`); it is read from the
 * list's own `offsetTop` after mount, once layout exists, rather than
 * hardcoded.
 *
 * Keeps real `<ul>`/`<li>` markup (with `role="list"`/`"listitem"`
 * doubled on, since Tailwind's preflight sets `list-style: none`, which
 * strips the implicit list role in some browsers) so the list stays as
 * accessible as the plain, un-virtualized version it replaces -- each
 * `<li>` is just absolutely positioned by the virtualizer instead of
 * sitting in normal flow.
 */
export function ItemList({ items, onOpen, onIncrement, onDecrement }: ItemListProps) {
  const listRef = useRef<HTMLUListElement>(null);
  const [scrollMargin, setScrollMargin] = useState(0);

  useLayoutEffect(() => {
    setScrollMargin(listRef.current?.offsetTop ?? 0);
  }, []);

  const virtualizer = useWindowVirtualizer({
    count: items.length,
    estimateSize: () => ESTIMATED_ROW_HEIGHT_PX,
    overscan: OVERSCAN_ROWS,
    scrollMargin,
    getItemKey: (index) => items[index].id,
  });

  return (
    <ul ref={listRef} role="list" className="relative" style={{ height: virtualizer.getTotalSize() }}>
      {virtualizer.getVirtualItems().map((virtualRow) => {
        const item = items[virtualRow.index];
        return (
          <li
            key={item.id}
            ref={virtualizer.measureElement}
            data-index={virtualRow.index}
            role="listitem"
            className="absolute top-0 left-0 w-full pb-2"
            style={{ transform: `translateY(${virtualRow.start - scrollMargin}px)` }}
          >
            <ItemRow item={item} onOpen={onOpen} onIncrement={onIncrement} onDecrement={onDecrement} />
          </li>
        );
      })}
    </ul>
  );
}
