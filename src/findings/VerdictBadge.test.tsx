import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { VerdictBadge } from "./VerdictBadge";

describe("VerdictBadge", () => {
  it("renders known judgment verdicts", () => {
    const html = renderToStaticMarkup(<VerdictBadge verdict="uphold" kind="judgment" />);
    expect(html).toContain("Uphold");
    expect(html).toContain("verdict-uphold");
  });

  it("renders handoff approve/defer/reject", () => {
    expect(renderToStaticMarkup(<VerdictBadge verdict="approve" kind="handoff" />)).toContain(
      "Approve",
    );
    expect(renderToStaticMarkup(<VerdictBadge verdict="defer" kind="handoff" />)).toContain("Defer");
    expect(renderToStaticMarkup(<VerdictBadge verdict="reject" kind="handoff" />)).toContain(
      "Reject",
    );
  });

  it("degrades gracefully when verdict is missing", () => {
    const html = renderToStaticMarkup(<VerdictBadge verdict={null} />);
    expect(html).toContain("No verdict");
    expect(html).toContain("verdict-unknown");
  });

  it("shows raw value for unknown verdict strings", () => {
    const html = renderToStaticMarkup(<VerdictBadge verdict="custom_flag" />);
    expect(html).toContain("custom_flag");
  });
});
