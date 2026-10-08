import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { ThermalPageStyle } from "./ThermalPageStyle";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ThermalPageStyle", () => {
  it("falls back to the 297mm page height before the content is measured", () => {
    // Defect this catches: jsdom's `getBoundingClientRect` always returns
    // 0 (it has no layout engine), the same gap the receipt's own
    // Receipt58Page.tsx guards against -- emitting `58mm 0mm` would print
    // a blank or truncated document.
    render(
      <ThermalPageStyle>
        <p>contenido</p>
      </ThermalPageStyle>,
    );

    expect(screen.getByText("contenido")).toBeInTheDocument();
    const styleTag = document.querySelector("style");
    expect(styleTag?.textContent).toBe("@page { size: 58mm 297mm; margin: 0; }");
  });

  it("emits the measured height once the content's rendered height resolves", () => {
    // Defect this catches: the measured height from a real browser's
    // layout never being applied to `@page`, leaving every print on the
    // tall 297mm fallback instead of the document's own actual height.
    vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockReturnValue({
      height: 192,
      width: 0,
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    });

    render(
      <ThermalPageStyle>
        <p>contenido</p>
      </ThermalPageStyle>,
    );

    const styleTag = document.querySelector("style");
    // 192px / (96px/in / 25.4mm/in) = 50.8mm.
    expect(styleTag?.textContent).toBe("@page { size: 58mm 50.8mm; margin: 0; }");
  });
});
