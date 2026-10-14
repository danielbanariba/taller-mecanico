import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useDelayedFlag } from "./useDelayedFlag";

const DELAY_MS = 600;

describe("useDelayedFlag", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("stays false for a condition that clears before the delay elapses", () => {
    // Defect this catches: without the delay gate, a fast sync (well under
    // 600ms) would still flash "Sincronizando..." on screen -- the exact
    // page flicker this task removes.
    const { result, rerender } = renderHook(({ active }) => useDelayedFlag(active, DELAY_MS), {
      initialProps: { active: true },
    });

    act(() => {
      vi.advanceTimersByTime(DELAY_MS - 1);
    });
    expect(result.current).toBe(false);

    rerender({ active: false });
    act(() => {
      vi.advanceTimersByTime(DELAY_MS);
    });
    expect(result.current).toBe(false);
  });

  it("becomes true once the condition has stayed active for the full delay", () => {
    // Defect this catches: an implementation that never schedules the
    // timer (or shows immediately, which the test above already rejects)
    // would leave a genuinely slow sync silent forever, with no way for
    // the mechanic to tell it is still running.
    const { result } = renderHook(() => useDelayedFlag(true, DELAY_MS));

    act(() => {
      vi.advanceTimersByTime(DELAY_MS);
    });

    expect(result.current).toBe(true);
  });

  it("flips back to false as soon as the condition clears, even after becoming true", () => {
    // Defect this catches: a flag that never resets (e.g. a ref set once)
    // would keep showing a stale "Sincronizando..." message after a later,
    // independent sync had already finished.
    const { result, rerender } = renderHook(({ active }) => useDelayedFlag(active, DELAY_MS), {
      initialProps: { active: true },
    });

    act(() => {
      vi.advanceTimersByTime(DELAY_MS);
    });
    expect(result.current).toBe(true);

    rerender({ active: false });
    expect(result.current).toBe(false);
  });
});
