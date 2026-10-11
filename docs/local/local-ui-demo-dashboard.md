# local-ui-demo-dashboard

**Status:** active  
**Updated:** 2026-10-10  
**Related:** [local-arch-orchestrator.md](local-arch-orchestrator.md), [local-arch-judging-agents.md](local-arch-judging-agents.md), [local-agent-reporter.md](local-agent-reporter.md), issues #28, #34

## Summary

The demo UI is SPECTRE's visual centerpiece — a real-time dashboard showing agent conversations, findings with optional judge verdicts, handoff graph, repo status, and live report preview as the crew audits a GitHub repository.

## Context

The research demo must be **compelling to watch**. Viewers should see agents talk, findings accumulate, handoffs occur with rationale, and advisory judges surface uphold/approve/accept-style badges — without exposing raw LLM chain-of-thought.

## Implementation

### Visual identity

Design tokens live as CSS variables in `src/app/app.css`:

| Token | Role |
|-------|------|
| `--bg-base` / `--bg-panel` | Charcoal atmosphere + translucent panels |
| `--signal` | Copper accent (brand / active state) |
| `--font-display` | Syne — brand + panel titles |
| `--font-body` | Source Sans 3 |
| `--font-mono` | IBM Plex Mono — evidence, chips, status |

Motion: panel rise-in, chat/handoff slide-in, running status pulse. Respects `prefers-reduced-motion`.

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│  SPECTRE (hero brand)     repo @ branch · scope    [status] │
├─────────────────────────────────────────────────────────────┤
│  Start audit controls · Halt · Past sessions                │
├──────────────────────┬──────────────────────────────────────┤
│  CREW CHANNEL        │  FINDINGS (+ judgment badges)        │
│  HANDOFFS (+ verdict)│  LIVE REPORT (+ report verdict)      │
└──────────────────────┴──────────────────────────────────────┘
```

### Source layout

```
src/
  app/App.tsx, app.css
  crew/AgentChatPanel.tsx, AgentAvatar.tsx, HandoffGraph.tsx
  findings/FindingsTimeline.tsx, FindingCard.tsx, SeverityBadge.tsx, VerdictBadge.tsx
  target/ScopeBanner.tsx, HaltButton.tsx
  report/LiveReportPanel.tsx
  hooks/useEngagementStream.ts
  lib/agents.ts
```

### WebSocket event routing

| Event type | UI effect |
|------------|-----------|
| `agent_message` | Crew channel (judge agents get distinct styling) |
| `finding` (security types) | Findings timeline |
| `finding` (`type=judgment`) | Matched onto cards via `evidence.reviewed_finding_id` |
| `handoff_decision` | Handoff list (stores event `id`) |
| `handoff_verdict` | Badge on matching `decision_id` |
| `report_section` | Live report |
| `report_verdict` | Badge on report / sections |
| `engagement_halted` / `complete` | Banner status |

Missing verdicts degrade to “No verdict” or omit the badge.

### Agent visual identity

| Agent | Role | Accent |
|-------|------|--------|
| Recon | crew | blue |
| VulnHunter | crew | copper |
| Exploiter | crew | rust |
| Reporter | crew | green |
| Finding / Handoff / Report Judge | judge | muted bronze + `judge` chip |

## Tests

| Case | Type |
|------|------|
| FindingCard severity + GitHub link | Positive |
| VerdictBadge known / unknown / missing | Positive + negatives |
| applyEvent attaches handoff + report verdicts | Positive |
| applyEvent ignores unknown decision_id | Negative |
| Judgments stored separately from findings | Positive |
| HaltButton disabled when idle | Negative |
| HandoffGraph empty state | Negative |

## Changelog

- 2026-10-10 — Visual redesign + judge verdict badges (#28, #34)
- 2026-06-25 — Initial demo UI doc
