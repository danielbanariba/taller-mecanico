import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// `useOfflineSync` and `useOnlineStatus` are mocked here, not driven through
// the real outbox/MSW stack like `useOfflineSync.test.tsx` and
// `ItemDetailPage.test.tsx` do: this test needs fake timers to assert on the
// 600ms delay, and combining fake timers with MSW's fetch interception and
// the `fake-indexeddb` polyfill risks a deadlock (a promise waiting on a
// real timer the fake clock never advances). Mocking both hooks keeps this
// test to the one thing it is isolating -- the container's delay gate --
// while `useDelayedFlag.test.ts` covers the gate itself in full.
const useOnlineStatusMock = vi.hoisted(() => vi.fn(() => false));
vi.mock("../../shared/offline/useOnlineStatus", () => ({
  useOnlineStatus: useOnlineStatusMock,
}));

const useOfflineSyncMock = vi.hoisted(() => vi.fn());
vi.mock("./hooks", () => ({
  useOfflineSync: useOfflineSyncMock,
}));

import { OfflineStatusBanner } from "./OfflineStatusBanner";

describe("OfflineStatusBanner", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    useOnlineStatusMock.mockReturnValue(false);
  });

  afterEach(() => {
    vi.useRealTimers();
    useOfflineSyncMock.mockReset();
    useOnlineStatusMock.mockReset();
  });

  it("never shows the pending count or syncing message for a flush that clears before the delay", () => {
    // Defect this catches: rendering `pendingCount`/`syncing` straight from
    // `useOfflineSync` with no delay gate would flash the banner on every
    // stock tap, even when the flush finishes in well under a second --
    // the exact page flicker T3 fixes.
    useOfflineSyncMock.mockReturnValue({ pendingCount: 1, syncing: true, lastErrorMessage: undefined });
    const { rerender } = render(<OfflineStatusBanner workshopId="w1" />);

    act(() => {
      vi.advanceTimersByTime(300);
    });
    // Still inside the delay window: must not be visible yet.
    expect(screen.queryByText("Sincronizando...")).not.toBeInTheDocument();
    expect(screen.queryByText("1 cambio por enviar")).not.toBeInTheDocument();

    useOfflineSyncMock.mockReturnValue({ pendingCount: 0, syncing: false, lastErrorMessage: undefined });
    rerender(<OfflineStatusBanner workshopId="w1" />);

    act(() => {
      vi.advanceTimersByTime(1000);
    });

    expect(screen.queryByText("Sincronizando...")).not.toBeInTheDocument();
    expect(screen.queryByText("1 cambio por enviar")).not.toBeInTheDocument();
  });

  it("shows the pending count once it has stayed queued past the delay", () => {
    // Defect this catches: an overly aggressive or inverted delay gate
    // would hide a genuinely stuck sync from the mechanic forever, leaving
    // them unsure whether their tap was ever saved.
    useOfflineSyncMock.mockReturnValue({ pendingCount: 2, syncing: false, lastErrorMessage: undefined });
    render(<OfflineStatusBanner workshopId="w1" />);

    act(() => {
      vi.advanceTimersByTime(600);
    });

    expect(screen.getByText("2 cambios por enviar")).toBeInTheDocument();
  });

  it("shows the offline message immediately, with no delay", () => {
    // Defect this catches: routing the offline message through the same
    // delay gate as the sync status would hide "Sin conexión..." from the
    // mechanic for 600ms right when they most need to see it.
    useOnlineStatusMock.mockReturnValue(true);
    useOfflineSyncMock.mockReturnValue({ pendingCount: 0, syncing: false, lastErrorMessage: undefined });
    render(<OfflineStatusBanner workshopId="w1" />);

    expect(screen.getByText("Sin conexión. Los cambios se guardan en el teléfono.")).toBeInTheDocument();
  });
});
