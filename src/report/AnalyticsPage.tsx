import { useMemo, useState } from "react";
import type {
  AgentMessage,
  Finding,
  HandoffDecision,
  ReportSection,
  ReportVerdict,
  EngagementMeta,
} from "../types/events";
import { FindingsTimeline } from "../findings/FindingsTimeline";
import { HandoffGraph } from "../crew/HandoffGraph";
import { LiveReportPanel } from "./LiveReportPanel";
import { AgentChatPanel } from "../crew/AgentChatPanel";

interface Props {
  meta: EngagementMeta | null;
  status: string;
  sessionId: string | null;
  findings: Finding[];
  judgments: Finding[];
  handoffs: HandoffDecision[];
  reportSections: ReportSection[];
  reportVerdict: ReportVerdict | null;
  messages: AgentMessage[];
  repo: string;
  branch: string;
  onRunAnother: () => void;
  onWatchTimeline: () => void;
}

export function AnalyticsPage({
  meta,
  status,
  sessionId,
  findings,
  judgments,
  handoffs,
  reportSections,
  reportVerdict,
  messages,
  repo,
  branch,
  onRunAnother,
  onWatchTimeline,
}: Props) {
  const [crewOpen, setCrewOpen] = useState(false);
  const severityCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const f of findings) {
      if (f.severity === "info") continue;
      counts[f.severity] = (counts[f.severity] ?? 0) + 1;
    }
    return counts;
  }, [findings]);

  return (
    <div className="analytics-page">
      <section className="analytics-hero">
        <p className="brand-mark compact">SPECTRE</p>
        <h1 className="analytics-title">Audit results</h1>
        <p className="brand-tag">
          {meta
            ? `${meta.repo} @ ${meta.branch}${meta.scopeName ? ` · ${meta.scopeName}` : ""}`
            : `${repo} @ ${branch}`}
        </p>
        <div className="analytics-meta">
          <span className={`status-pill ${status}`}>{status}</span>
          {sessionId ? <span className="session-chip">{sessionId}</span> : null}
        </div>
        <ul className="severity-summary">
          {["critical", "high", "medium", "low"].map((sev) => (
            <li key={sev}>
              <span className="sev-label">{sev}</span>
              <strong>{severityCounts[sev] ?? 0}</strong>
            </li>
          ))}
        </ul>
        <div className="analytics-actions">
          <button type="button" className="primary-btn" onClick={onRunAnother}>
            Run another audit
          </button>
          <button type="button" onClick={onWatchTimeline}>
            Watch timeline again
          </button>
        </div>
      </section>

      <section className="analytics-section">
        <FindingsTimeline
          findings={findings}
          judgments={judgments}
          repo={repo}
          branch={branch}
        />
      </section>

      <section className="analytics-section">
        <HandoffGraph handoffs={handoffs} />
      </section>

      <section className="analytics-section analytics-report">
        <LiveReportPanel sections={reportSections} reportVerdict={reportVerdict} />
      </section>

      <section className="analytics-section">
        <button
          type="button"
          className="disclosure-btn"
          onClick={() => setCrewOpen((open) => !open)}
          aria-expanded={crewOpen}
        >
          {crewOpen ? "Hide crew channel" : "Show crew channel"}
        </button>
        {crewOpen ? <AgentChatPanel messages={messages} /> : null}
      </section>
    </div>
  );
}
