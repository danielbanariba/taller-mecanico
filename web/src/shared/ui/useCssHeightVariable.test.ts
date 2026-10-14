import { createElement } from "react";
import { render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useCssHeightVariable } from "./useCssHeightVariable";

type ResizeCallback = () => void;

/**
 * jsdom has no real `ResizeObserver` (and no real layout): this stubs the
 * global with a fake that captures the one callback the hook under test
 * registers, so a test can trigger a "resize" on demand.
 */
function stubResizeObserver() {
  let callback: ResizeCallback | undefined;

  class FakeResizeObserver {
    constructor(cb: ResizeCallback) {
      callback = cb;
    }
    observe = vi.fn();
    unobserve = vi.fn();
    disconnect = vi.fn();
  }

  vi.stubGlobal("ResizeObserver", FakeResizeObserver);
  return { trigger: () => callback?.() };
}

const VARIABLE_NAME = "--test-height";

// `.ts`, not `.tsx` -- `createElement` instead of JSX keeps this a plain
// TypeScript module, matching this hook's sibling `useDelayedFlag.test.ts`.
function Measured() {
  const ref = useCssHeightVariable<HTMLDivElement>(VARIABLE_NAME);
  return createElement("div", { ref }, "content");
}

describe("useCssHeightVariable", () => {
  beforeEach(() => {
    document.documentElement.style.removeProperty(VARIABLE_NAME);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    document.documentElement.style.removeProperty(VARIABLE_NAME);
  });

  it("publishes the observed element's current height as a CSS variable on mount", () => {
    // Defect this catches: a hook that never reads `getBoundingClientRect`
    // (or writes to the wrong element/property) would leave the variable
    // unset, and every consumer's `calc()` fallback would silently stand in
    // forever instead of the real measurement.
    stubResizeObserver();
    vi.spyOn(HTMLDivElement.prototype, "getBoundingClientRect").mockReturnValue({ height: 57 } as DOMRect);

    render(createElement(Measured));

    expect(document.documentElement.style.getPropertyValue(VARIABLE_NAME)).toBe("57px");
  });

  it("re-publishes the height when the observed element resizes", () => {
    // Defect this catches: capturing the height once at mount instead of
    // re-measuring from the ResizeObserver's own callback would leave the
    // variable stuck at the first value -- e.g. the sync toast growing
    // from one line to two would never update `--sync-toast-height`.
    const { trigger } = stubResizeObserver();
    const rect = vi.spyOn(HTMLDivElement.prototype, "getBoundingClientRect").mockReturnValue({
      height: 57,
    } as DOMRect);

    render(createElement(Measured));
    rect.mockReturnValue({ height: 79 } as DOMRect);
    trigger();

    expect(document.documentElement.style.getPropertyValue(VARIABLE_NAME)).toBe("79px");
  });

  it("resets the variable to 0px on unmount", () => {
    // Defect this catches: skipping cleanup would leave a stale height
    // published after the element unmounts -- e.g. navigating from a route
    // with the bottom nav to a receipt route without one would keep
    // reserving space for a nav that is no longer on screen.
    stubResizeObserver();
    vi.spyOn(HTMLDivElement.prototype, "getBoundingClientRect").mockReturnValue({ height: 80 } as DOMRect);

    const { unmount } = render(createElement(Measured));
    unmount();

    expect(document.documentElement.style.getPropertyValue(VARIABLE_NAME)).toBe("0px");
  });
});
