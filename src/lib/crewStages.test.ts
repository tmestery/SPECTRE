import { describe, expect, it } from "vitest";
import {
  recentCrewMessages,
  resolveActiveCrewAgent,
  stageIndex,
} from "./crewStages";

describe("crewStages", () => {
  it("resolves active crew agent from activation", () => {
    expect(
      resolveActiveCrewAgent({
        activeAgent: "recon",
        messages: [],
        handoffs: [],
      }),
    ).toBe("recon");
  });

  it("falls back to last crew message when activation missing", () => {
    expect(
      resolveActiveCrewAgent({
        activeAgent: null,
        messages: [
          { agent: "recon" },
          { agent: "finding_judge" },
          { agent: "vuln_hunter" },
        ],
        handoffs: [],
      }),
    ).toBe("vuln_hunter");
  });

  it("falls back to handoff target", () => {
    expect(
      resolveActiveCrewAgent({
        activeAgent: "finding_judge",
        messages: [],
        handoffs: [{ to_agent: "exploiter" }],
      }),
    ).toBe("exploiter");
  });

  it("caps recent crew messages and skips judges", () => {
    const recent = recentCrewMessages(
      [
        { agent: "recon", id: "1" },
        { agent: "finding_judge", id: "2" },
        { agent: "vuln_hunter", id: "3" },
        { agent: "exploiter", id: "4" },
        { agent: "reporter", id: "5" },
        { agent: "reporter", id: "6" },
      ],
      4,
    );
    expect(recent.map((m) => m.id)).toEqual(["3", "4", "5", "6"]);
  });

  it("returns -1 stage index for unknown agents", () => {
    expect(stageIndex("not_an_agent")).toBe(-1);
    expect(stageIndex(null)).toBe(-1);
  });
});
