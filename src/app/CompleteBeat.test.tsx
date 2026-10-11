import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { CompleteBeat } from "./CompleteBeat";

describe("CompleteBeat", () => {
  it("renders complete copy", () => {
    const html = renderToStaticMarkup(
      <CompleteBeat status="complete" durationMs={10_000} onDone={() => undefined} />,
    );
    expect(html).toContain("Audit complete");
  });

  it("renders halted copy", () => {
    const html = renderToStaticMarkup(
      <CompleteBeat status="halted" durationMs={10_000} onDone={vi.fn()} />,
    );
    expect(html).toContain("Halted");
  });
});
