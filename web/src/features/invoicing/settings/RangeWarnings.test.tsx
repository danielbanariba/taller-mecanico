import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { RangeWarnings } from "./RangeWarnings";
import type { DocumentReadinessOut } from "../api";

function readiness(overrides: Partial<DocumentReadinessOut> = {}): DocumentReadinessOut {
  return {
    document_type: "01",
    ready: true,
    blocked_reason: null,
    active_range_id: "range-1",
    next_number: "001-001-01-00000001",
    warnings: [],
    ...overrides,
  };
}

describe("RangeWarnings", () => {
  it("renders the fecha-límite warning's days-left Spanish text", () => {
    // Defect this catches: a range within 60 days of its fecha límite
    // (AD-18, Art. 59's 2-month request window) giving the owner no
    // signal to request the next CAI range in time.
    render(<RangeWarnings documents={[readiness({ warnings: [{ code: "range_expires_soon", days_left: 60 }] })]} />);

    expect(screen.getByText(/vence en 60 día\(s\)/)).toBeInTheDocument();
  });

  it("renders the low-remaining-numbers warning's remaining-count Spanish text", () => {
    // Defect this catches: a range running low on numbers (AD-18's
    // design-fixed threshold) giving the owner no signal before it
    // actually blocks issuance (AD-6's exhaustion check).
    render(<RangeWarnings documents={[readiness({ warnings: [{ code: "range_low_numbers", remaining: 10 }] })]} />);

    expect(screen.getByText(/quedan 10 números/i)).toBeInTheDocument();
  });

  it("renders nothing when no document carries a warning", () => {
    // Defect this catches: a stale or placeholder warning banner shown
    // for a workshop whose ranges are all comfortably far from either
    // threshold.
    const { container } = render(<RangeWarnings documents={[readiness()]} />);

    expect(container).toBeEmptyDOMElement();
  });
});
