# local-ui-demo-dashboard

**Status:** active  
**Updated:** 2026-06-26  
**Related:** [local-arch-orchestrator.md](local-arch-orchestrator.md), [local-agent-reporter.md](local-agent-reporter.md)

## Summary

The demo UI is SPECTRE's visual centerpiece — a real-time dashboard showing agent conversations, findings timeline with **file links**, handoff graph, repo status, and live report preview as the crew audits a GitHub repository.

## Context

The research demo must be **compelling to watch**. Viewers should see agents "talk," findings accumulate, and handoffs occur with visible rationale — without exposing raw LLM chain-of-thought.

## Implementation

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│  SPECTRE  │  tmestery/SPECTRE @ main  │  [HALT]            │
├──────────────────────┬──────────────────────────────────────┤
│  AGENT CHAT          │  FINDINGS TIMELINE                   │
│  ┌─────────────────┐ │  ● Recon — 36 files, 2 workflows     │
│  │ Recon: Mapping  │ │  ● VulnHunter — secret in config.ts  │
│  │ ...             │ │  ● Exploiter — key validated (live)  │
│  └─────────────────┘ │  ● Reporter — drafting summary      │
├──────────────────────┤                                      │
│  HANDOFF GRAPH       │  LIVE REPORT                         │
│  Recon → Vuln → ...  │  Findings with GitHub permalinks...  │
└──────────────────────┴──────────────────────────────────────┘
```

### Source layout

```
src/
  app/
    App.tsx
    AppState.tsx
    app.css
  crew/
    AgentChatPanel.tsx
    AgentAvatar.tsx
    HandoffGraph.tsx
  findings/
    FindingsTimeline.tsx
    FindingCard.tsx
    SeverityBadge.tsx
  target/
    ScopeBanner.tsx
    TargetStatus.tsx
    HaltButton.tsx
  report/
    LiveReportPanel.tsx
  hooks/
    useEngagementStream.ts   # WebSocket
```

### WebSocket integration

```typescript
// useEngagementStream.ts
// Connect to ws://localhost:8765/sessions/<id>
// On event: route by type to chat, timeline, graph, report
```

Event routing:

| Event type | Component |
|------------|-----------|
| `agent_message` | AgentChatPanel |
| `finding` | FindingsTimeline |
| `handoff_decision` | HandoffGraph |
| `report_section` | LiveReportPanel |
| `engagement_halted` | HaltButton + banner |

### Agent visual identity

| Agent | Color | Icon |
|-------|-------|------|
| Recon | Blue | Radar |
| VulnHunter | Amber | Magnifier |
| Exploiter | Red | Bolt |
| Reporter | Green | Document |

### Art direction

- **Dark terminal aesthetic** — fits security tooling vibe
- **Monospace for evidence** — tool output in code blocks
- **Animated handoff edges** — graph highlights on new handoff_decision
- **Severity colors** — consistent with finding schema
- Not a generic chat UI — should feel like a mission control panel

### Phase 3 deliverables

1. Reporter agent streams `report_section` events and writes `reports/<session>.md` + `.html`
2. WebSocket live stream (all engagement event types)
3. Halt button + CLI `spectre halt --session` via signal file
4. Demo UI dashboard with chat, timeline, handoffs, live report

## Tests

| Case | Type |
|------|------|
| FindingCard renders severity badge correctly | Positive |
| useEngagementStream reconnects on disconnect | Negative |
| HaltButton disabled when no active session | Negative |
| Timeline sorts events by timestamp | Negative |
| HandoffGraph renders empty state | Negative |

## Changelog

- 2026-06-25 — Initial demo UI doc
