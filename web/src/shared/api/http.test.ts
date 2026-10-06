import { describe, expect, it } from "vitest";
import { http as mockHttp, HttpResponse } from "msw";

import { server } from "../../test/server";
import { ApiError, http } from "./http";

describe("http", () => {
  it("throws ApiError with the API's detail as the code on a non-2xx JSON response", async () => {
    server.use(
      mockHttp.post("/api/auth/login", () =>
        HttpResponse.json({ detail: "invalid_credentials" }, { status: 401 }),
      ),
    );

    try {
      await http.post("/api/auth/login", { phone: "99998888", password: "wrong" });
      expect.fail("expected http.post to throw");
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).status).toBe(401);
      expect((error as ApiError).code).toBe("invalid_credentials");
    }
  });

  it("throws ApiError with code network_error when the request never reaches the server", async () => {
    server.use(mockHttp.post("/api/auth/login", () => HttpResponse.error()));

    try {
      await http.post("/api/auth/login", { phone: "99998888", password: "x" });
      expect.fail("expected http.post to throw");
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).code).toBe("network_error");
    }
  });
});
