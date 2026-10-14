import { useLayoutEffect, useRef, type RefObject } from "react";

/**
 * Publishes the rendered height of the returned ref's element -- via
 * `getBoundingClientRect`, so padding, borders and any safe-area inset
 * padding all count -- as a CSS custom property on `document.documentElement`,
 * kept live through a `ResizeObserver` for as long as the element stays
 * mounted. Resets the variable to `"0px"` on unmount: a route that renders
 * neither `BottomNav` nor `OfflineStatusBanner` (a receipt or print layout)
 * must never leave a stale offset behind for whatever else reads the
 * variable.
 *
 * jsdom has no real `ResizeObserver` and no real layout, so this no-ops
 * when `ResizeObserver` is unavailable instead of throwing -- every
 * existing test that renders a consumer of this hook without stubbing one
 * keeps passing unchanged. Each call site's own `calc()` fallback covers
 * the variable staying unset in that case.
 */
export function useCssHeightVariable<T extends HTMLElement>(variableName: string): RefObject<T | null> {
  const ref = useRef<T | null>(null);

  useLayoutEffect(() => {
    const element = ref.current;
    if (!element || typeof ResizeObserver === "undefined") {
      return;
    }

    function publish(): void {
      // Non-null: `element` is narrowed above, but TS does not carry that
      // narrowing into a function declared (and invoked later, including
      // from the `ResizeObserver` callback) inside this same closure.
      document.documentElement.style.setProperty(variableName, `${element!.getBoundingClientRect().height}px`);
    }

    publish();
    const observer = new ResizeObserver(publish);
    observer.observe(element);

    return () => {
      observer.disconnect();
      document.documentElement.style.setProperty(variableName, "0px");
    };
  }, [variableName]);

  return ref;
}
