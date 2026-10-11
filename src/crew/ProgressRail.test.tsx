import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { ProgressRail } from "./ProgressRail";

describe("ProgressRail", () => {
  it("marks completed and active stages", () => {
    const html = renderToStaticMarkup(<ProgressRail activeAgent="exploiter" />);
    expect(html).toContain("is-done");
    expect(html).toContain("is-active");
    expect(html).toContain("Exploiter");
  });

  it("does not crash on unknown agent", () => {
    const html = renderToStaticMarkup(<ProgressRail activeAgent="unknown_bot" />);
    expect(html).toContain("progress-rail");
    expect(html).not.toContain("is-active");
  });
});
