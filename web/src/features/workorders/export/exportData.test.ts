import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from "vitest";
import { http, HttpResponse } from "msw";

import { server } from "../../../test/server";
import { exportData } from "./exportData";

describe("exportData", () => {
  let createObjectURL: Mock<(obj: Blob | MediaSource) => string>;
  let revokeObjectURL: Mock<(url: string) => void>;
  let clickSpy: ReturnType<typeof vi.spyOn>;
  let downloadAttribute: string | undefined;

  beforeEach(() => {
    downloadAttribute = undefined;
    createObjectURL = vi.fn<(obj: Blob | MediaSource) => string>(() => "blob:mock-url");
    revokeObjectURL = vi.fn<(url: string) => void>();
    URL.createObjectURL = createObjectURL;
    URL.revokeObjectURL = revokeObjectURL;
    clickSpy = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (this: HTMLAnchorElement) {
      downloadAttribute = this.download;
    });
  });

  afterEach(() => {
    clickSpy.mockRestore();
  });

  it("downloads the ZIP through a temporary anchor, using the server's own filename, then revokes the object URL", async () => {
    // Defect this catches: a leaked object URL (never revoked) piling up
    // across repeated exports, or a download attribute that ignores the
    // server's own `Content-Disposition` filename.
    server.use(
      http.get("/api/export", () =>
        new HttpResponse(new Blob(["zip-bytes"], { type: "application/zip" }), {
          headers: { "Content-Disposition": 'attachment; filename="taller-export-2026-10-07.zip"' },
        }),
      ),
    );

    await exportData();

    expect(createObjectURL).toHaveBeenCalledTimes(1);
    expect(clickSpy).toHaveBeenCalledTimes(1);
    expect(downloadAttribute).toBe("taller-export-2026-10-07.zip");
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:mock-url");
  });

  it("maps a 401 to the existing session-expired error code, not a generic failure", async () => {
    // Defect this catches: an expired session surfacing as an unlabeled
    // failure the user cannot act on, instead of the "sign in again"
    // message every other feature's `copy.ts` already maps.
    server.use(http.get("/api/export", () => HttpResponse.json({ detail: "not_authenticated" }, { status: 401 })));

    await expect(exportData()).rejects.toMatchObject({ code: "not_authenticated" });
    expect(createObjectURL).not.toHaveBeenCalled();
  });

  it("maps a failed fetch to network_error instead of an unhandled rejection", async () => {
    // Defect this catches: an offline/DNS failure during export bubbling
    // up as a raw fetch `TypeError` the UI has no mapped message for.
    server.use(http.get("/api/export", () => HttpResponse.error()));

    await expect(exportData()).rejects.toMatchObject({ code: "network_error" });
    expect(createObjectURL).not.toHaveBeenCalled();
  });
});
