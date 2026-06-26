import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { FindingCard } from "../findings/FindingCard";
import { HaltButton } from "../target/HaltButton";
import { HandoffGraph } from "../crew/HandoffGraph";
import { sortEventsByTimestamp } from "../lib/sort";

describe("FindingCard", () => {
  it("renders severity badge and github link", () => {
    const html = renderToStaticMarkup(
      <FindingCard
        repo="tmestery/SPECTRE"
        branch="main"
        finding={{
          id: "fnd_1",
          type: "secret",
          agent: "vuln_hunter",
          target: "tmestery/SPECTRE:src/config.ts",
          severity: "high",
          confidence: 0.9,
          title: "AWS key",
          evidence: { file: "src/config.ts", line: 14, snippet_redacted: "AKIA****" },
          status: "tentative",
          created_at: "2026-06-26T00:00:00Z",
        }}
      />,
    );
    expect(html).toContain("high");
    expect(html).toContain("github.com/tmestery/SPECTRE/blob/main/src/config.ts#L14");
  });
});

describe("HaltButton", () => {
  it("is disabled when no active session", () => {
    const html = renderToStaticMarkup(<HaltButton disabled onHalt={() => undefined} />);
    expect(html).toContain("disabled");
  });
});

describe("HandoffGraph", () => {
  it("renders empty state", () => {
    const html = renderToStaticMarkup(<HandoffGraph handoffs={[]} />);
    expect(html).toContain("No handoffs yet");
  });
});

describe("sortEventsByTimestamp", () => {
  it("sorts events chronologically", () => {
    const sorted = sortEventsByTimestamp([
      { timestamp: "2026-06-26T02:00:00Z", message: "b", agent: "recon" },
      { timestamp: "2026-06-26T01:00:00Z", message: "a", agent: "recon" },
    ]);
    expect(sorted[0].message).toBe("a");
  });
});
