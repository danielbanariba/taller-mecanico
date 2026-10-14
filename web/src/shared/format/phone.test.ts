import { describe, expect, it } from "vitest";

import { formatPhone, isValidPhone } from "./phone";

describe("formatPhone", () => {
  it("groups a normalized phone as 4-4 so it reads like a local number", () => {
    expect(formatPhone("30000002")).toBe("3000-0002");
  });

  it("leaves a value that is not a normalized 8-digit phone untouched", () => {
    expect(formatPhone("+504 3000")).toBe("+504 3000");
  });
});

describe("isValidPhone", () => {
  // Mirrors `api/tests/identity/test_phone_number.py` exactly: the web
  // form must reject nothing the API would accept, and accept nothing
  // the API would reject.
  it("accepts a plain local number", () => {
    expect(isValidPhone("99887766")).toBe(true);
  });

  it.each(["9988-7766", "9988 7766", " 99887766 ", "99-88-77-66"])(
    "accepts %s, normalizing spaces and dashes",
    (raw) => {
      expect(isValidPhone(raw)).toBe(true);
    },
  );

  it.each(["+504 9988-7766", "+50499887766", "504 9988 7766", "50499887766"])(
    "accepts %s, stripping the country-code prefix",
    (raw) => {
      expect(isValidPhone(raw)).toBe(true);
    },
  );

  it.each(["998877", "998877661", "+504998877"])(
    // Defect this catches: a form that submits a too-short or too-long
    // phone instead of blocking it before the round trip.
    "rejects %s for having the wrong length",
    (raw) => {
      expect(isValidPhone(raw)).toBe(false);
    },
  );

  it.each(["09887766", "19887766"])(
    // Defect this catches: a form that accepts a first digit Honduras
    // never issues (0 or 1), which the API would still reject.
    "rejects %s for a leading zero or one",
    (raw) => {
      expect(isValidPhone(raw)).toBe(false);
    },
  );

  it("rejects letters", () => {
    // Defect this catches: a form that lets non-digit characters through
    // to a round trip the API can only reject.
    expect(isValidPhone("9988A766")).toBe(false);
  });
});
