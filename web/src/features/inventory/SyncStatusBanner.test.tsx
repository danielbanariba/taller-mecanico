import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { SyncStatusBanner } from "./SyncStatusBanner";

describe("SyncStatusBanner", () => {
  it("shows the offline message and the pending count together when offline with queued entries", () => {
    // Defect this catches: showing only one of the two signals would hide
    // from the mechanic either that they are offline, or that taps they
    // already made have not reached the server yet.
    render(<SyncStatusBanner isOffline pendingCount={3} syncing={false} />);

    expect(screen.getByText("Sin conexión. Los cambios se guardan en el teléfono.")).toBeInTheDocument();
    expect(screen.getByText("3 cambios por enviar")).toBeInTheDocument();
  });

  it("renders nothing when online, nothing pending, and no error", () => {
    // Defect this catches: a banner that always renders something would
    // permanently take up space on every screen even when there is
    // nothing the mechanic needs to know.
    const { container } = render(<SyncStatusBanner isOffline={false} pendingCount={0} syncing={false} />);

    expect(container).toBeEmptyDOMElement();
  });

  it("shows the last definitive error message when one is set", () => {
    render(
      <SyncStatusBanner isOffline={false} pendingCount={0} syncing={false} lastErrorMessage="No se encontró el repuesto." />,
    );

    expect(screen.getByText("No se encontró el repuesto.")).toBeInTheDocument();
  });
});
