import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { DemoBand } from "./DemoBand";

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("DemoBand", () => {
  it("shows the demo watermark on a build compiled with the demo configuration", () => {
    // Defect this catches: a demo-deployed build printing a Factura that
    // looks indistinguishable from a real fiscal document
    // (`fiscal-document-print` spec's "The demo build shows the watermark").
    vi.stubEnv("VITE_DEMO_PHONE", "9999-9999");
    vi.stubEnv("VITE_DEMO_PASSWORD", "demo1234");

    render(<DemoBand />);

    expect(screen.getByText("DEMOSTRACIÓN — SIN VALOR FISCAL")).toBeInTheDocument();
  });

  it("shows no watermark on a build without the demo configuration", () => {
    // Defect this catches: a real build accidentally carrying the demo
    // watermark on a legally required document
    // (`fiscal-document-print` spec's "A non-demo build shows no watermark").
    vi.stubEnv("VITE_DEMO_PHONE", undefined);
    vi.stubEnv("VITE_DEMO_PASSWORD", undefined);

    const { container } = render(<DemoBand />);

    expect(container).toBeEmptyDOMElement();
  });
});
