import { onlineManager } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { http as httpClient } from "../api/http";
import { server } from "../../test/server";
import { PROBE_INTERVAL_MS, reportNetworkError } from "./reachability";

function stubNavigatorOnline(online: boolean): void {
  Object.defineProperty(window.navigator, "onLine", { configurable: true, get: () => online });
}

describe("reachability", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    Reflect.deleteProperty(window.navigator, "onLine");
    onlineManager.setOnline(true);
  });

  it("reports offline after a network error, then online again once the health probe succeeds", async () => {
    // Defect this catches: bb889c5's `markOfflineOnNetworkError` called
    // `onlineManager.setOnline(false)` directly and nothing ever called it
    // back -- recovery relied solely on the browser's own `online` event,
    // which never fires when `navigator.onLine` stayed true the whole time
    // (a mid-deploy API restart, a tunnel hiccup). Against that code this
    // test is RED forever: nothing in it ever turns `isOnline()` back true.
    server.use(http.get("/api/health", () => HttpResponse.json({ status: "ok", database: "ok" })));

    reportNetworkError();
    expect(onlineManager.isOnline()).toBe(false);

    await vi.advanceTimersByTimeAsync(PROBE_INTERVAL_MS);

    expect(onlineManager.isOnline()).toBe(true);
  });

  it("keeps probing and stays offline while /api/health keeps failing", async () => {
    // Defect this catches: a probe loop that stops after one failed attempt
    // (or that treats a rejected/non-ok response as success) would leave
    // the app stuck offline even once the server comes back on a later try.
    let calls = 0;
    server.use(
      http.get("/api/health", () => {
        calls += 1;
        return HttpResponse.error();
      }),
    );

    reportNetworkError();

    await vi.advanceTimersByTimeAsync(PROBE_INTERVAL_MS);
    expect(onlineManager.isOnline()).toBe(false);
    expect(calls).toBe(1);

    await vi.advanceTimersByTimeAsync(PROBE_INTERVAL_MS);
    expect(onlineManager.isOnline()).toBe(false);
    expect(calls).toBe(2);
  });

  it("never sends a probe while the browser itself reports no connection", async () => {
    // Defect this catches: probing while `navigator.onLine` is false burns
    // a request that cannot possibly succeed (the OS itself says there is
    // no link). No `/api/health` handler is registered in this test at
    // all, so with strict MSW (`onUnhandledFrame: "error"`, `setup.ts`'s
    // `request:unhandled` check) any probe fired here fails the test.
    stubNavigatorOnline(false);

    reportNetworkError();
    await vi.advanceTimersByTimeAsync(PROBE_INTERVAL_MS * 2);

    expect(onlineManager.isOnline()).toBe(false);
  });

  it("does not restore online status from an unrelated successful request", async () => {
    // Defect this catches: wiring recovery to any successful request --
    // e.g. having `shared/api/http.ts`'s shared wrapper itself call
    // `onlineManager.setOnline(true)` on every 2xx, instead of only this
    // module's own dedicated `/api/health` probe -- would flip the whole
    // app back online from a request that has nothing to do with
    // reachability, reintroducing the exact flapping bb889c5's comment
    // warned against.
    server.use(http.get("/api/unrelated", () => HttpResponse.json({ ok: true })));

    reportNetworkError();
    await httpClient.get("/api/unrelated");

    expect(onlineManager.isOnline()).toBe(false);
  });
});
