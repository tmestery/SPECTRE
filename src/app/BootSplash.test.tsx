import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { BootSplash } from "./BootSplash";

describe("BootSplash", () => {
  it("shows connecting status", () => {
    const html = renderToStaticMarkup(<BootSplash status="connecting" />);
    expect(html).toContain("SPECTRE");
    expect(html).toContain("Connecting to orchestrator");
  });

  it("shows retry when errored", () => {
    const html = renderToStaticMarkup(
      <BootSplash status="error" errorMessage="offline" onRetry={() => undefined} />,
    );
    expect(html).toContain("offline");
    expect(html).toContain("Retry");
  });
});
