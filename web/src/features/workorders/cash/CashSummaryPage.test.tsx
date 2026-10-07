import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { onlineManager } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";

import { formatCents } from "../../../shared/format/money";
import { renderWithQueryClient } from "../../../test/render";
import { server } from "../../../test/server";
import { CashSummaryPage } from "./CashSummaryPage";
import type { CashSummaryOut } from "../api";

/**
 * `formatCents` inserts a non-breaking space between the currency symbol
 * and the amount; `@testing-library/dom`'s own text normalizer collapses
 * it to a plain space before comparing, so the matcher has to go through
 * the same normalization (mirrors `receipt/ReceiptBody.test.tsx`'s own
 * helper).
 */
function money(cents: number): string {
  return formatCents(cents).replace(/\u00a0/g, " ");
}

const SESSION_RESPONSE = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

const SUMMARY: CashSummaryOut = {
  date: "2026-10-07",
  totals_cents: { cash: 30000, transfer: 15000, card: 0, other: 0 },
  total_cents: 45000,
  payments: [
    { id: "p1", order_id: "o1", order_number: 3, amount_cents: 30000, method: "cash", paid_at: "2026-10-07T12:00:00Z" },
  ],
};

function mockSessionAndSummary() {
  server.use(
    http.get("/api/auth/me", () => HttpResponse.json(SESSION_RESPONSE)),
    http.get("/api/cash-summary", () => HttpResponse.json(SUMMARY)),
  );
}

describe("CashSummaryPage", () => {
  it("renders today's totals broken down by payment method, and the day's payments", async () => {
    // Defect this catches: a mixed-method total (cash, transfer, zero
    // card/other) rendered wrong, or a listed payment missing its order
    // number for drawer reconciliation (the `daily-cash-summary` spec).
    mockSessionAndSummary();
    renderWithQueryClient(<CashSummaryPage />);

    expect(await screen.findByText(money(30000))).toBeInTheDocument();
    expect(screen.getByText(money(15000))).toBeInTheDocument();
    expect(screen.getByText(money(45000))).toBeInTheDocument();
    expect(screen.getByText("Orden #3")).toBeInTheDocument();
  });

  it("shows the offline message instead of a previously-fetched total once the connection drops", async () => {
    // Defect this catches: a cash total already held in memory from
    // before the connection dropped being shown as though it were still
    // current (AD-17: the summary must always be a live read).
    mockSessionAndSummary();
    renderWithQueryClient(<CashSummaryPage />);

    expect(await screen.findByText("L 450.00")).toBeInTheDocument();

    onlineManager.setOnline(false);

    expect(await screen.findByText("El corte de caja requiere conexión a internet.")).toBeInTheDocument();
    expect(screen.queryByText("L 450.00")).not.toBeInTheDocument();
  });
});
