import { describe, expect, it } from "vitest";
import { applyEvent, type EngagementState } from "./useEngagementStream";
import type { BusEvent } from "../types/events";

function baseState(): EngagementState {
  return {
    connected: true,
    ready: true,
    sessionId: "eng_1",
    meta: null,
    messages: [],
    findings: [],
    judgments: [],
    handoffs: [],
    reportSections: [],
    reportVerdict: null,
    status: "running",
    error: null,
    defaults: null,
    scopes: [],
    sessions: [],
    activeSession: "eng_1",
    githubTokenConfigured: true,
    llmConfigured: true,
    llmProvider: null,
    llmModel: null,
  };
}

function event(partial: Partial<BusEvent> & Pick<BusEvent, "type" | "payload">): BusEvent {
  return {
    id: partial.id ?? "evt_1",
    type: partial.type,
    session_id: "eng_1",
    sequence_num: partial.sequence_num ?? 1,
    payload: partial.payload,
    timestamp: partial.timestamp ?? "2026-10-10T00:00:00Z",
  };
}

describe("applyEvent verdict wiring", () => {
  it("attaches handoff_verdict to matching handoff decision", () => {
    let state = applyEvent(
      baseState(),
      event({
        id: "h1",
        type: "handoff_decision",
        payload: {
          rule: "repo_mapped",
          from_agent: "recon",
          to_agent: "vuln_hunter",
          rationale: "mapped",
        },
      }),
    );
    state = applyEvent(
      state,
      event({
        id: "v1",
        type: "handoff_verdict",
        payload: {
          decision_id: "h1",
          verdict: "approve",
          rationale: "ok",
          advisory: true,
        },
      }),
    );
    expect(state.handoffs[0].verdict?.verdict).toBe("approve");
  });

  it("stores judgment findings separately from security findings", () => {
    let state = applyEvent(
      baseState(),
      event({
        type: "finding",
        payload: {
          finding: {
            id: "fnd_1",
            type: "secret",
            agent: "vuln_hunter",
            target: "x",
            severity: "high",
            confidence: 0.9,
            title: "secret",
            evidence: {},
            status: "tentative",
            created_at: "2026-10-10T00:00:00Z",
          },
        },
      }),
    );
    state = applyEvent(
      state,
      event({
        type: "finding",
        payload: {
          finding: {
            id: "j1",
            type: "judgment",
            agent: "finding_judge",
            target: "x",
            severity: "info",
            confidence: 1,
            title: "Judgment: uphold",
            evidence: { verdict: "uphold", reviewed_finding_id: "fnd_1", rationale: "y" },
            status: "tentative",
            created_at: "2026-10-10T00:00:01Z",
          },
        },
      }),
    );
    expect(state.findings).toHaveLength(1);
    expect(state.judgments).toHaveLength(1);
    expect(state.judgments[0].evidence.verdict).toBe("uphold");
  });

  it("ignores handoff_verdict for unknown decision ids", () => {
    const state = applyEvent(
      baseState(),
      event({
        type: "handoff_verdict",
        payload: { decision_id: "missing", verdict: "reject", rationale: "x" },
      }),
    );
    expect(state.handoffs).toHaveLength(0);
  });

  it("records report_verdict on sections", () => {
    let state = applyEvent(
      baseState(),
      event({
        type: "report_section",
        payload: { section_id: "exec", title: "Exec", markdown: "# hi" },
      }),
    );
    state = applyEvent(
      state,
      event({
        type: "report_verdict",
        payload: {
          report_section_ids: ["exec"],
          verdict: "revise",
          issues: ["tone"],
          rationale: "tighten",
          advisory: true,
        },
      }),
    );
    expect(state.reportVerdict?.verdict).toBe("revise");
    expect(state.reportSections[0].verdict?.verdict).toBe("revise");
  });
});
