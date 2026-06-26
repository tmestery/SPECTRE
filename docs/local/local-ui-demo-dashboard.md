# local-ui-demo-dashboard

**Status:** draft  
**Updated:** 2026-06-25  
**Related:** [local-arch-orchestrator.md](local-arch-orchestrator.md), [local-agent-reporter.md](local-agent-reporter.md)

## Summary

The demo UI is SPECTRE's visual centerpiece — a real-time dashboard showing agent conversations, findings timeline, handoff graph, target status, and live report preview as the crew progresses through a lab engagement.

## Context

The research demo must be **compelling to watch**. Viewers should see agents "talk," findings accumulate, and handoffs occur with visible rationale — without exposing raw LLM chain-of-thought.

## Implementation

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│  SPECTRE  │  Target: DVWA (127.0.0.1:4280)  │  [HALT]       │
├──────────────────────┬──────────────────────────────────────┤
│  AGENT CHAT          │  FINDINGS TIMELINE                   │
│  ┌─────────────────┐ │  ● 12:00 Recon — port 4280 open      │
│  │ Recon: Scanning │ │  ● 12:01 Recon — DVWA detected       │
│  │ ...             │ │  ● 12:03 VulnHunter — SQLi found     │
│  └─────────────────┘ │  ● 12:05 Exploiter — DB extracted    │
├──────────────────────┤                                      │
│  HANDOFF GRAPH       │  LIVE REPORT                         │
│  Recon → Vuln → ...  │  Executive summary streaming...      │
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

1. Static shell with mock data
2. WebSocket live stream
3. Halt button wired to orchestrator
4. Report panel with markdown render

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
