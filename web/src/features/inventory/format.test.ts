import { describe, expect, it } from "vitest";

import { centsToPlainAmount, formatCents, parseLempirasToCents } from "./format";

describe("parseLempirasToCents", () => {
  it("parses a plain integer with no separators", () => {
    expect(parseLempirasToCents("1250")).toBe(125000);
  });

  it("parses a dot decimal separator", () => {
    expect(parseLempirasToCents("125.50")).toBe(12550);
  });

  it("reads a single comma followed by 1-2 digits as the decimal separator", () => {
    // Ambiguity rule: "125,50" has no dot, so the comma is the decimal
    // separator, not a thousands group.
    expect(parseLempirasToCents("125,50")).toBe(12550);
    expect(parseLempirasToCents("1,5")).toBe(150);
  });

  it("reads a comma followed by exactly 3 digits as a thousands separator", () => {
    // Defect this catches: the previous regex rejected any amount with a
    // comma followed by 3 digits, so a user retyping a price exactly as
    // `formatCents` displays it (grouped thousands) got "invalid".
    expect(parseLempirasToCents("1,250")).toBe(125000);
    expect(parseLempirasToCents("1,250.00")).toBe(125000);
  });

  it("accepts multiple thousands groups with a dot decimal separator", () => {
    expect(parseLempirasToCents("12,345,678.9")).toBe(1234567890);
  });

  it("rejects malformed grouping", () => {
    // "1,25,0" has a comma followed by only 2 digits before another comma:
    // neither a valid thousands group (needs exactly 3 digits) nor a
    // trailing decimal (a comma decimal can't be followed by more digits).
    expect(parseLempirasToCents("1,25,0")).toBeUndefined();
  });

  it("rejects more than 2 decimal digits", () => {
    expect(parseLempirasToCents("125.555")).toBeUndefined();
  });

  it("rejects letters", () => {
    expect(parseLempirasToCents("abc")).toBeUndefined();
  });

  it("rejects negative amounts", () => {
    expect(parseLempirasToCents("-125.50")).toBeUndefined();
  });

  it("returns null for empty input", () => {
    expect(parseLempirasToCents("")).toBeNull();
    expect(parseLempirasToCents("   ")).toBeNull();
  });
});

describe("formatCents / parseLempirasToCents round trip", () => {
  it.each([0, 550, 12550, 125000, 1234567890])("round-trips %i cents through formatCents", (cents) => {
    const plain = centsToPlainAmount(cents);
    expect(parseLempirasToCents(plain)).toBe(cents);
    // formatCents's grouped output must itself be accepted back, since
    // that's exactly what a user retyping the displayed value sees.
    const formatted = formatCents(cents).replace(/^[^\d-]+/, "");
    expect(parseLempirasToCents(formatted)).toBe(cents);
  });
});
