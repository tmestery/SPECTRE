import type { EngagementMeta, Finding, AgentMessage, HandoffDecision } from "../types/events";
import { HaltButton } from "../target/HaltButton";
import { resolveActiveCrewAgent } from "../lib/crewStages";
import { ProgressRail } from "./ProgressRail";
import { LiveStage } from "./LiveStage";
import { LatestDiscovery } from "./LatestDiscovery";

interface Props {
  meta: EngagementMeta | null;
  sessionId: string | null;
  status: string;
  activeAgent: string | null;
  messages: AgentMessage[];
  findings: Finding[];
  judgments: Finding[];
  handoffs: HandoffDecision[];
  repo: string;
  branch: string;
  canHalt: boolean;
  readOnly?: boolean;
  onHalt: () => void;
}

export function LiveCinemaView({
  meta,
  sessionId,
  status,
  activeAgent,
  messages,
  findings,
  judgments,
  handoffs,
  repo,
  branch,
  canHalt,
  readOnly = false,
  onHalt,
}: Props) {
  const resolved = resolveActiveCrewAgent({ activeAgent, messages, handoffs });

  return (
    <div className="live-cinema">
      <header className="live-cinema-bar">
        <div className="live-cinema-identity">
          <p className="brand-mark compact">SPECTRE</p>
          <p className="brand-tag">
            {meta
              ? `${meta.repo} @ ${meta.branch}${meta.scopeName ? ` · ${meta.scopeName}` : ""}`
              : `${repo} @ ${branch}`}
          </p>
        </div>
        <div className="live-cinema-actions">
          {sessionId ? <span className="session-chip">{sessionId}</span> : null}
          <span className={`status-pill ${status}`}>{status}</span>
          {!readOnly ? <HaltButton disabled={!canHalt} onHalt={onHalt} /> : null}
        </div>
      </header>

      <ProgressRail activeAgent={resolved} />

      <div className="live-cinema-body">
        <LiveStage activeAgent={resolved} messages={messages} readOnly={readOnly} />
        <LatestDiscovery
          findings={findings}
          judgments={judgments}
          repo={repo}
          branch={branch}
        />
      </div>
    </div>
  );
}
