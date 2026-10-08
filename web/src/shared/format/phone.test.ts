import { describe, expect, it } from "vitest";

import { formatPhone } from "./phone";

describe("formatPhone", () => {
  it("groups a normalized phone as 4-4 so it reads like a local number", () => {
    expect(formatPhone("30000002")).toBe("3000-0002");
  });

  it("leaves a value that is not a normalized 8-digit phone untouched", () => {
    expect(formatPhone("+504 3000")).toBe("+504 3000");
  });
});
